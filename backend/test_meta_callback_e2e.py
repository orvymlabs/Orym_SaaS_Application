"""
End-to-end HTTP test of the Meta OAuth callback flow against the REAL FastAPI app.

Uses an isolated SQLite database (never touches the production Postgres) and a
mocked MetaOAuthService so no request reaches Meta.

Covers:
  1. GET  /api/integrations/meta/config            -> app_id + config_id
  2. POST /api/integrations/meta/oauth/callback    -> success path saves integration
  3. POST /api/integrations/meta/oauth/callback    -> error path returns 400 with Meta message
  4. POST callback without auth                     -> 401
  5. GET  /health                                   -> app alive
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
async def fake_setup_success(self, code, redirect_uri=None):
    assert code and redirect_uri, "code and redirect_uri must be forwarded to the service"
    return True, {
        "access_token": "EAA_test_token",
        "business_id": "waba_111",
        "waba_id": "waba_111",
        "business_name": "Test Business",
        "phone_number_id": "phone_222",
        "display_phone_number": "+15551234567",
    }, None

async def fake_setup_error(self, code, redirect_uri=None):
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
    redirect_uri = "https://apps.orvym.com/dashboard/integrations"
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": code, "redirect_uri": redirect_uri},
        headers=headers,
    )
    check("callback returns 200", r.status_code == 200, f"{r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        body = r.json()
        check("response success true", body.get("success") is True, str(body))
        check("phone number echoed", body.get("data", {}).get("phone_number") == "+15551234567", str(body))

        # Verify the integration row was saved
        db = SessionLocal()
        try:
            saved = db.query(Integration).filter(Integration.bot_id == bot.id).first()
            check("integration saved has_whatsapp_token", bool(saved.whatsapp_token), str(saved.whatsapp_token)[:20])
            check("phone_number_id saved", saved.phone_number_id == "phone_222", str(saved.phone_number_id))
            check("whatsapp_number saved", saved.whatsapp_number == "+15551234567", str(saved.whatsapp_number))
            check("verify_token generated", bool(saved.verify_token), "")
        finally:
            db.close()

    print("=== TEST 5: POST callback ERROR path (Meta 400 style) ===")
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_error
    code2 = "AQ" + "y" * 449
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": code2, "redirect_uri": "https://apps.orvym.com/dashboard/integrations"},
        headers=headers,
    )
    check("callback returns 400 on Meta error", r.status_code == 400, str(r.status_code))
    if r.status_code == 400:
        detail = r.json().get("detail", "")
        check("Meta error message propagated", "redirect_uri is identical" in detail, detail[:120])

    print("=== TEST 6: POST callback missing redirect_uri (service sees None) ===")
    calls = {}
    async def fake_setup_record(self, code, redirect_uri=None):
        calls["redirect_uri"] = redirect_uri
        return True, {
            "access_token": "EAA_t2", "business_id": "waba_333", "waba_id": "waba_333",
            "phone_number_id": "phone_444", "display_phone_number": "+19998887777",
        }, None
    RouterMetaOAuthService.setup_whatsapp_integration = fake_setup_record
    r = client.post(
        "/api/integrations/meta/oauth/callback",
        json={"code": "AQzzz"},
        headers=headers,
    )
    check("callback 200 without redirect_uri", r.status_code == 200, str(r.status_code))
    check("service received redirect_uri=None", calls.get("redirect_uri") is None, str(calls))

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
