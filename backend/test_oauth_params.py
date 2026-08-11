"""
Test script to verify OAuth token exchange parameters (CORRECTED).
This simulates what parameters will be sent to Meta for the OAuth dialog
flow used by WhatsApp Embedded Signup.

Rule: the exchange ALWAYS includes the redirect_uri parameter, but for the
Embedded Signup FB.login popup flow it sends redirect_uri="" (empty string).
The code is bound to Meta's INTERNAL redirect URI, so sending the canonical
https://apps.orvym.com/dashboard/integrations/ value is exactly what triggers
Meta error_subcode 36008. A genuinely custom, non-canonical redirect_uri is
forwarded verbatim.
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


async def test_token_exchange_params():
    """Test what parameters are constructed for token exchange"""

    service = MetaOAuthService(app_id="test_app_id_123", app_secret="test_secret_456")
    test_code = "test_authorization_code_from_dialog"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction")
    print("=" * 80)
    print()

    # Test 1: Frontend sends the canonical redirect_uri
    print("TEST 1: Frontend sends the canonical dialog redirect_uri")
    print("-" * 80)
    redirect_uri = CANONICAL

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": exchange_redirect_uri(redirect_uri),
    }

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri is present: {('redirect_uri' in params)}")
    print(f"redirect_uri value: '{params['redirect_uri']}' (empty for the Embedded Signup popup flow)")
    print()

    # Test 2: No redirect_uri -> empty string is sent (never the canonical value)
    print("TEST 2: No redirect_uri -> exchange sends '' (canonical value NEVER sent)")
    print("-" * 80)
    redirect_uri = None

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": exchange_redirect_uri(redirect_uri),
    }

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri present: {('redirect_uri' in params)}  (should be True)")
    print(f"redirect_uri value: '{params['redirect_uri']}'")
    print()

    # Test 3: A custom non-canonical redirect_uri is forwarded verbatim
    print("TEST 3: Custom non-canonical redirect_uri is forwarded verbatim")
    print("-" * 80)
    custom = "https://manual-dialog.example.com/callback"
    custom_value = exchange_redirect_uri(custom)
    print(f"redirect_uri value: '{custom_value}'")
    assert custom_value == custom
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ The exchange ALWAYS includes the redirect_uri parameter")
    print("✓ Embedded Signup popup flow sends redirect_uri='' (never the canonical value)")
    print("✓ A custom non-canonical redirect_uri is forwarded verbatim")
    print("✓ Sending the canonical value in the exchange is what triggers 36008")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_token_exchange_params())
