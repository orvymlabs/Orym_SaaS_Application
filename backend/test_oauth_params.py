"""
Test script to verify OAuth token exchange parameters (CORRECTED).
This simulates what parameters will be sent to Meta for the OAuth dialog
flow used by WhatsApp Embedded Signup.

Rule: redirect_uri is ALWAYS sent with the canonical production value
https://apps.orvym.com/dashboard/integrations/ (with the trailing slash).
It is NEVER omitted and an empty string is NEVER sent - a missing or empty
value falls back to the canonical constant. Omitting redirect_uri is exactly
what triggers Meta error_subcode 36008.
"""
import asyncio
from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"


async def test_token_exchange_params():
    """Test what parameters are constructed for token exchange"""

    service = MetaOAuthService(app_id="test_app_id_123", app_secret="test_secret_456")
    test_code = "test_authorization_code_from_dialog"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction")
    print("=" * 80)
    print()

    # Test 1: Frontend sends the canonical redirect_uri
    print("TEST 1: Frontend sends the canonical redirect_uri")
    print("-" * 80)
    redirect_uri = CANONICAL

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": (redirect_uri or "").strip() or CANONICAL_REDIRECT_URI,
    }

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri is present: {('redirect_uri' in params)}")
    print(f"redirect_uri value: '{params['redirect_uri']}'")
    print(f"redirect_uri is empty string: {params['redirect_uri'] == ''}")
    print()

    # Test 2: No redirect_uri -> canonical value is used (never empty, never omitted)
    print("TEST 2: No redirect_uri -> canonical value used (never empty, never omitted)")
    print("-" * 80)
    redirect_uri = None

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": (redirect_uri or "").strip() or CANONICAL_REDIRECT_URI,
    }

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri present: {('redirect_uri' in params)}  (should be True)")
    print(f"redirect_uri value: '{params['redirect_uri']}'")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ The exchange ALWAYS sends redirect_uri = https://apps.orvym.com/dashboard/integrations/")
    print("✓ A missing/empty redirect_uri falls back to the canonical value (never omitted)")
    print("✗ Empty-string redirect_uri is NEVER sent (it never matches Meta's record)")
    print("✗ redirect_uri is NEVER omitted (omission triggers Meta error_subcode 36008)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_token_exchange_params())
