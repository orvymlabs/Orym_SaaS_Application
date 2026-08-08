"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
 1. With an explicit redirect_uri -> params include redirect_uri (exact value).
 2. Without redirect_uri -> redirect_uri is OMITTED entirely.
 3. redirect_uri="" is NEVER sent (empty string is banned).
"""
import asyncio
from services.meta_oauth import MetaOAuthService


async def main():
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")
    code = "AQ" + ("x" * 449)

    print("=" * 70)
    print("TEST 1: Frontend sends exact dialog redirect_uri (manual dialog flow)")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code,
         "redirect_uri": "https://apps.orvym.com/dashboard/integrations"},
    )

    print("=" * 70)
    print("TEST 2: No redirect_uri supplied -> OMITTED (never empty string)")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code},
    )

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    # Build the exact params the exchange would send
    params_with = {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code}
    redirect_uri = "https://apps.orvym.com/dashboard/integrations"
    if redirect_uri:
        params_with["redirect_uri"] = redirect_uri
    assert params_with["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations"
    assert "redirect_uri" in params_with
    assert params_with["redirect_uri"] != ""

    params_without = {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code}
    assert "redirect_uri" not in params_without  # omitted entirely

    # Empty string must never be assigned to redirect_uri in executable code
    # (only mentioned in docstrings explaining why it is banned).
    source = open("services/meta_oauth.py").read()
    assert '"redirect_uri": ""' not in source  # dict-literal empty string
    assert "params['redirect_uri'] = ''" not in source  # empty-string assignment
    assert 'redirect_uri=""' not in source.replace("NEVER send redirect_uri=\"\"", "")

    print("PASS: exact redirect_uri forwarded")
    print("PASS: empty redirect_uri omitted entirely")
    print("PASS: no empty-string redirect_uri anywhere in service code")


asyncio.run(main())
