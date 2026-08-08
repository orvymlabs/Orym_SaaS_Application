"""
End-to-end HTTP test of the Meta OAuth callback flow against the REAL FastAPI app.

Uses an isolated SQLite database (never touches the production Postgres) and a
mocked MetaOAuthService so no request reaches Meta.

Covers:
  1. GET  /api/integrations/meta/config            -> app_id + config_id
  2. POST /api/integrations/meta/oauth/callback    -> success path saves integration
  3. POST /api/integrations/meta/oauth/callback    -> code-only (production payload)
     with no asset IDs; backend resolves WABA/phone/business server-side
  4. POST /api/integrations/meta/oauth/callback    -> error path returns 400 with Meta message
  5. POST callback without auth                     -> 401
  6. GET  /health                                   -> app alive
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

from config import get_settings
from database import init_db, SessionLocal, Base, engine
from models import User, Bot, Integration
from services.auth_service import create_access_token

from routers.integrations import MetaOAuthService as RouterMetaOAuthService

from main import app

settings = get_settings()

# Mock Meta entirely - never make a network call
async def fake_setup_success(self, code, redirect_uri=None, waba_id=None, phone_number_id=None, business_id=None):
    assert code, "code must be forwarded to the service"
    # Mirrors the real service: asset IDs are OPTIONAL. When Embedded Signup
    # does not deliver them (production SDK_QUERY_STRING payload has only the
    # code), the service resolves them server-side from the token.
    resolved_waba = waba_id or "waba_discovered_888"
    resolved_phone = phone_number_id or "phone_discovered_999"
    resolved_biz = business_id or "biz_discovered_777"
    return True, {
        "access_token": "EAA_test_token",
        "business_id": resolved_biz,
        "waba_id": resolved_waba,
        "business_name": "Test Business",
        "phone_number_id": resolved_phone,
        "display_phone_number": "+15551234567",
        "verified_name": "Test Business",
    }, None

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

    print("=== TEST 4b: POST callback CODE-ONLY (production SDK_QUERY_STRING payload) ===")
    # Production Meta payload delivers ONLY the exchangeable code - no asset
    # IDs. The backend must accept the code and resolve WABA/phone/business
    # server-side (the mocked service resolves them on behalf of the backend).
    code_only = "AQ" + "k" * 449
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": code_only, "redirect_uri": redirect_uri, "waba_id": "", "phone_number_id": "", "business_id": ""},
        headers=headers,
    )
    check("code-only callback returns 200", r.status_code == 200, f"{r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        body = r.json()
        check("code-only success true", body.get("success") is True, str(body))
        check("code-only waba_id resolved server-side", body.get("data", {}).get("waba_id") == "waba_discovered_888", str(body))
        check("code-only phone echoed", body.get("data", {}).get("phone_number") == "+15551234567", str(body))

        db = SessionLocal()
        try:
            saved = db.query(Integration).filter(Integration.bot_id == bot.id).first()
            check("code-only waba_id saved", saved.waba_id == "waba_discovered_888", str(saved.waba_id))
            check("code-only phone_number_id saved", saved.phone_number_id == "phone_discovered_999", str(saved.phone_number_id))
            check("code-only business_id saved", saved.business_id == "biz_discovered_777", str(saved.business_id))
        finally:
            db.close()

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

    print("=== TEST 6: POST callback missing redirect_uri (configured default is used) ===")
    calls = {}
    async def fake_setup_record(self, code, redirect_uri=None, waba_id=None, phone_number_id=None, business_id=None):
        calls["redirect_uri"] = redirect_uri
        calls["waba_id"] = waba_id
        return True, {
            "access_token": "EAA_t2", "business_id": "biz_444", "waba_id": waba_id,
            "phone_number_id": "phone_444", "display_phone_number": "+19998887777",
            "verified_name": "Verified Co",
        }, None
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_record
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": "AQ" + "z" * 449, "waba_id": "waba_555", "phone_number_id": "phone_444", "business_id": "biz_444"},
        headers=headers,
    )
    check("callback 200 without redirect_uri", r.status_code == 200, str(r.status_code))
    check(
        "service received the exact production redirect_uri",
        calls.get("redirect_uri") == settings.META_OAUTH_REDIRECT_URI,
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
