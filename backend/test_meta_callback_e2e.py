"""
End-to-end HTTP test of the Meta OAuth callback flow against the REAL FastAPI app.

Uses an isolated SQLite database (never touches the production Postgres) and a
mocked MetaOAuthService so no request reaches Meta.

Covers:
  1. GET  /api/integrations/meta/config            -> app_id + config_id
  2. POST /api/integrations/meta/oauth/callback    -> success path saves integration
  3. POST /api/integrations/meta/oauth/callback    -> code-only (production payload)
     with no asset IDs; backend resolves WABA/phone/business server-side
  4. POST /api/integrations/meta/oauth/callback    -> code-only with nothing
     resolvable fails with a controlled 400 WABA_NOT_RETURNED
  5. POST /api/integrations/meta/oauth/callback    -> error path returns 400 with Meta message
  6. POST callback without auth                     -> 401
  7. GET  /health                                   -> app alive
"""
import os
import sys
import json
import tempfile
from unittest import mock
from pathlib import Path

# MUST be set before any app import so config/database use an isolated SQLite DB
TEST_DB = Path(tempfile.mkdtemp(prefix="orvym_e2e_")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient
from fastapi.testclient import TestClient as _T

from database import init_db, SessionLocal, Base, engine
from models import User, Bot, Integration
from services.auth_service import create_access_token

from routers.integrations import MetaOAuthService as RouterMetaOAuthService

from main import app

# Mock Meta entirely - never make a network call
async def fake_setup_success(self, code, redirect_uri=None, waba_id=None, phone_number_id=None, business_id=None):
    assert code, "code must be forwarded to the service"
    # Mirrors the real service: the WABA ID and phone number ID come from the
    # WA_EMBEDDED_SIGNUP session event when it delivered them. When Meta did not
    # return them (code-only callback), the service resolves them server-side
    # via the documented fallback (/debug_token granular_scopes target_ids +
    # the WABA phone_numbers edge) instead of failing. The real service also
    # registers the phone (POST /<PHONE_NUMBER_ID>/register) after subscribing.
    resolved_waba = waba_id or "waba_111"
    resolved_phone = phone_number_id or "phone_222"
    resolved_biz = business_id or "biz_333"
    return True, {
        "access_token": "EAA_test_token",
        "business_id": resolved_biz,
        "waba_id": resolved_waba,
        "business_name": "Test Business",
        "phone_number_id": resolved_phone,
        "display_phone_number": "+15551234567",
        "verified_name": "Test Business",
        "phone_registered": True,
    }, None

async def fake_setup_no_resolution(self, code, redirect_uri=None, waba_id=None, phone_number_id=None, business_id=None):
    """Simulates the real service when NOTHING can be resolved (no session
    event IDs and no /debug_token granular_scopes target_ids) - the backend
    returns a controlled WABA_NOT_RETURNED error instead of guessing."""
    if not waba_id:
        return False, None, "WABA_NOT_RETURNED: the WhatsApp Business Account ID was not returned by Meta Embedded Signup. Please restart WhatsApp Embedded Signup and complete the setup again."
    if not phone_number_id:
        return False, None, "PHONE_NUMBER_NOT_RETURNED: the WhatsApp phone number was not returned by Meta Embedded Signup."
    return False, None, "unreachable"

async def fake_setup_error(self, code, redirect_uri=None, waba_id=None, phone_number_id=None, business_id=None):
    return False, None, "Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

# Patch the service class INSIDE the router module so the endpoint uses the mock
RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_success

results = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((name, cond))
    print(f"  [{status}] {name}" + (f"  -- {detail}" if detail and not cond else ""))


def main():
    print("Setting up isolated test DB...")
    assert init_db(), "init_db() failed"

    db = SessionLocal()
    try:
        user = User(email="e2e_test@example.com", password_hash="x", plan="starter")
        db.add(user)
        db.commit()
        db.refresh(user)

        bot = Bot(user_id=user.id)
        db.add(bot)
        db.commit()
        db.refresh(bot)

        integ = Integration(bot_id=bot.id)
        db.add(integ)
        db.commit()
        db.refresh(integ)
        user_id = user.id
        bot_id = bot.id
    finally:
        db.close()

    token = create_access_token({"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    print("=== TEST 1: Health check ===")
    r = client.get("/health")
    check("GET /health returns 200", r.status_code == 200, str(r.status_code))

    print("=== TEST 2: GET /api/integrations/meta/config ===")
    r = client.get("/api/integrations/meta/config")
    check("meta/config returns 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        body = r.json()
        check("config returns app_id", bool(body.get("app_id")), str(body))
        check("config returns config_id", bool(body.get("config_id")), str(body))

    print("=== TEST 3: POST callback WITHOUT auth -> 401 ===")
    r = client.post("/api/integrations/meta/oauth/callback", json={"code": "AQxyz"})
    check("401 returned for missing token", r.status_code == 401, str(r.status_code))

    print("=== TEST 4: POST callback SUCCESS path ===")
    code = "AQ" + "x" * 449
    redirect_uri = "https://apps.orvym.com/dashboard/integrations/"
    payload_success = {
        "code": code,
        "redirect_uri": redirect_uri,
        "waba_id": "waba_111",
        "phone_number_id": "phone_222",
        "business_id": "biz_333",
    }
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json=payload_success,
        headers=headers,
    )
    check("callback returns 200", r.status_code == 200, f"{r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        body = r.json()
        check("response success true", body.get("success") is True, str(body))
        check("phone number echoed", body.get("data", {}).get("phone_number") == "+15551234567", str(body))
        check("waba_id echoed", body.get("data", {}).get("waba_id") == "waba_111", str(body))
        check("phone_registered echoed", body.get("phone_registered") is True, str(body))

        # Verify the integration row was saved
        db = SessionLocal()
        try:
            saved = db.query(Integration).filter(Integration.bot_id == bot.id).first()
            check("integration saved has_whatsapp_token", bool(saved.whatsapp_token), str(saved.whatsapp_token)[:20])
            check("phone_number_id saved", saved.phone_number_id == "phone_222", str(saved.phone_number_id))
            check("whatsapp_number saved", saved.whatsapp_number == "+15551234567", str(saved.whatsapp_number))
            check("waba_id saved", saved.waba_id == "waba_111", str(saved.waba_id))
            check("business_id saved", saved.business_id == "biz_333", str(saved.business_id))
            check("verified_name saved", saved.verified_name == "Test Business", str(saved.verified_name))
            check("connection_status saved", saved.connection_status == "connected", str(saved.connection_status))
            check("verify_token generated", bool(saved.verify_token), "")
        finally:
            db.close()

    print("=== TEST 4b: POST callback CODE-ONLY (missing session IDs) ===")
    # Production Meta payload delivers ONLY the exchangeable code - no asset
    # IDs (the WA_EMBEDDED_SIGNUP session event was delayed/unavailable). The
    # backend must NOT stall or fail: it exchanges the code and resolves the
    # WABA/phone IDs server-side using the documented Meta fallback
    # (/debug_token granular_scopes target_ids + the WABA phone_numbers edge).
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_success
    code_only = "AQ" + "k" * 449
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": code_only, "redirect_uri": redirect_uri, "waba_id": "", "phone_number_id": "", "business_id": ""},
        headers=headers,
    )
    check("code-only callback returns 200 (server-side resolution)", r.status_code == 200, f"{r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        body = r.json()
        check("code-only response success true", body.get("success") is True, str(body))
        check("code-only waba_id resolved", body.get("data", {}).get("waba_id") == "waba_111", str(body))
        check("code-only phone_number_id resolved", body.get("data", {}).get("phone_number_id") == "phone_222", str(body))

    print("=== TEST 4b2: POST callback CODE-ONLY with NOTHING resolvable ===")
    # If neither the session event NOR the /debug_token granular_scopes
    # target_ids can produce a WABA ID, the backend returns a controlled 400
    # WABA_NOT_RETURNED - it NEVER guesses an ID or uses /me/businesses.
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_no_resolution
    code_only2 = "AQ" + "m" * 449
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": code_only2, "redirect_uri": redirect_uri, "waba_id": "", "phone_number_id": "", "business_id": ""},
        headers=headers,
    )
    check("unresolvable code-only callback returns 400", r.status_code == 400, f"{r.status_code} {r.text[:300]}")
    if r.status_code == 400:
        detail = r.json().get("detail", "")
        check("unresolvable error is WABA_NOT_RETURNED", "WABA_NOT_RETURNED" in detail, detail[:120])

    print("=== TEST 4c: POST callback - duplicate authorization code rejected ===")
    # A Meta authorization code is single-use. The same code must NEVER reach
    # the backend twice. The idempotency ledger records the code hash before the
    # exchange, so a duplicate callback is rejected with 409
    # OAUTH_CODE_ALREADY_PROCESSED and the code is never exchanged twice.
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_success
    dup_code = "AQ" + "p" * 449
    payload_dup = {
        "code": dup_code,
        "redirect_uri": redirect_uri,
        "waba_id": "waba_dup_111",
        "phone_number_id": "phone_dup_222",
        "business_id": "biz_dup_333",
    }
    r1 = client.post("/api/integrations/meta/oauth/callback", json=payload_dup, headers=headers)
    check("first submission of code returns 200", r1.status_code == 200, f"{r1.status_code} {r1.text[:200]}")
    r2 = client.post("/api/integrations/meta/oauth/callback", json=payload_dup, headers=headers)
    check("duplicate code rejected with 409", r2.status_code == 409, f"{r2.status_code} {r2.text[:200]}")
    if r2.status_code == 409:
        check("duplicate detail is OAUTH_CODE_ALREADY_PROCESSED", "OAUTH_CODE_ALREADY_PROCESSED" in r2.json().get("detail", ""), r2.json().get("detail", "")[:120])

    print("=== TEST 5: POST callback ERROR path (Meta 400 style) ===")
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_error
    code2 = "AQ" + "y" * 449
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={**payload_success, "code": code2},
        headers=headers,
    )
    check("callback returns 400 on Meta error", r.status_code == 400, str(r.status_code))
    if r.status_code == 400:
        detail = r.json().get("detail", "")
        check("Meta error message propagated", "redirect_uri is identical" in detail, detail[:120])

    print("=== TEST 6: POST callback - frontend redirect_uri is NEVER forwarded to the service ===")
    calls = {}
    async def fake_setup_record(self, code, waba_id=None, phone_number_id=None, business_id=None, **kwargs):
        calls["redirect_uri"] = kwargs.get("redirect_uri")
        calls["waba_id"] = waba_id
        return True, {
            "access_token": "EAA_t2", "business_id": "biz_444", "waba_id": waba_id or "waba_555",
            "phone_number_id": "phone_444", "display_phone_number": "+19998887777",
            "verified_name": "Verified Co",
        }, None
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_record
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={
            "code": "AQ" + "z" * 449,
            "redirect_uri": "https://apps.orvym.com/dashboard/integrations/",
            "waba_id": "waba_555", "phone_number_id": "phone_444", "business_id": "biz_444",
        },
        headers=headers,
    )
    check("callback 200 with redirect_uri in payload", r.status_code == 200, str(r.status_code))
    check(
        "frontend redirect_uri NOT forwarded to the service (per Meta's current docs the exchange never sends redirect_uri)",
        calls.get("redirect_uri") is None,
        str(calls),
    )
    check("service received waba_id from Embedded Signup", calls.get("waba_id") == "waba_555", str(calls))

    print()
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    failed = [name for name, ok in results if not ok]
    if failed:
        print("FAILED:", failed)
        sys.exit(1)
    print("ALL HTTP END-TO-END TESTS PASSED")


if __name__ == "__main__":
    main()
