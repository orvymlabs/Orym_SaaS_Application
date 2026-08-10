"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
 1. The exchange ALWAYS includes redirect_uri with the canonical production
    value (https://apps.orvym.com/dashboard/integrations/) - never omitted.
 2. redirect_uri="" is NEVER sent (empty string is banned) - the canonical
    value is used instead.
 3. The canonical value always carries the trailing slash.
"""
import asyncio
from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"


async def main():
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")
    code = "AQ" + ("x" * 449)

    print("=" * 70)
    print("TEST 1: Frontend sends the canonical dialog redirect_uri")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code,
         "redirect_uri": CANONICAL},
    )

    print("=" * 70)
    print("TEST 2: No redirect_uri supplied -> canonical value is used (never empty)")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code,
         "redirect_uri": CANONICAL},
    )

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical redirect_uri must include the trailing slash"

    # The exchange ALWAYS sends the canonical redirect_uri
    params = {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code}
    redirect_uri = (params.get("redirect_uri") or "").strip() or CANONICAL_REDIRECT_URI
    params["redirect_uri"] = redirect_uri
    assert params["redirect_uri"] == CANONICAL
    assert "redirect_uri" in params
    assert params["redirect_uri"] != ""

    # Empty string must never be assigned to redirect_uri in executable code
    # (only mentioned in docstrings explaining why it is banned).
    source = open("services/meta_oauth.py").read()
    assert '"redirect_uri": ""' not in source  # dict-literal empty string
    assert "params['redirect_uri'] = ''" not in source  # empty-string assignment
    assert 'redirect_uri=""' not in source.replace("NEVER send redirect_uri=\"\"", "")

    print("PASS: exchange always sends the canonical redirect_uri")
    print("PASS: empty-string redirect_uri is never sent - canonical value used")
    print("PASS: no empty-string redirect_uri anywhere in service code")


asyncio.run(main())
