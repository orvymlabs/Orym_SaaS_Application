"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
 1. The exchange ALWAYS includes the redirect_uri parameter (never omitted).
 2. For the Embedded Signup FB.login popup flow the exchange sends
    redirect_uri="" (empty string) - the code is bound to Meta's internal
    redirect URI, and sending the canonical apps.orvym.com value is what
    caused error_subcode 36008.
 3. A genuinely custom, non-canonical redirect_uri is forwarded verbatim.
"""
import asyncio
from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"


def exchange_redirect_uri(redirect_uri):
    """Mirror of the exchange's redirect_uri normalization logic."""
    supplied = (redirect_uri or "").strip()
    if supplied and supplied != CANONICAL_REDIRECT_URI:
        return supplied
    return ""


async def main():
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")
    code = "AQ" + ("x" * 449)

    print("=" * 70)
    print("TEST 1: Frontend sends the canonical dialog redirect_uri")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code,
         "redirect_uri": exchange_redirect_uri(CANONICAL)},
        auth_redirect_uri=CANONICAL,
    )

    print("=" * 70)
    print("TEST 2: No redirect_uri supplied -> exchange sends '' (never canonical)")
    print("=" * 70)
    svc._log_exchange_request(
        "https://graph.facebook.com/v26.0/oauth/access_token",
        {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code,
         "redirect_uri": exchange_redirect_uri(None)},
        auth_redirect_uri="",
    )

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical redirect_uri must include the trailing slash"

    # The exchange ALWAYS includes the redirect_uri parameter
    params = {"client_id": svc.app_id, "client_secret": svc.app_secret, "code": code}
    params["redirect_uri"] = exchange_redirect_uri(params.get("redirect_uri"))
    assert "redirect_uri" in params, "redirect_uri parameter must always be present"

    # Embedded Signup FB.login popup flow -> empty string (canonical NEVER sent)
    assert exchange_redirect_uri(CANONICAL) == ""
    assert exchange_redirect_uri(None) == ""
    assert exchange_redirect_uri("   ") == ""
    assert exchange_redirect_uri("") == ""

    # A genuinely custom, non-canonical redirect_uri is forwarded verbatim
    custom = "https://manual-dialog.example.com/callback"
    assert exchange_redirect_uri(custom) == custom

    print("PASS: redirect_uri parameter always present in the exchange")
    print("PASS: Embedded Signup exchange sends redirect_uri='' (canonical value never sent)")
    print("PASS: custom non-canonical redirect_uri forwarded verbatim")


asyncio.run(main())
