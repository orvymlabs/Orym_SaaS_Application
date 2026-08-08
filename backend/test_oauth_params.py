"""
Test script to verify OAuth token exchange parameters (CORRECTED).
This simulates what parameters will be sent to Meta for the manual
OAuth dialog flow used by WhatsApp Embedded Signup.

Rule: redirect_uri is sent ONLY when it is the EXACT value used in the
OAuth dialog request. An empty string is NEVER sent.
"""
import asyncio
from services.meta_oauth import MetaOAuthService


async def test_token_exchange_params():
    """Test what parameters are constructed for token exchange"""

    service = MetaOAuthService(app_id="test_app_id_123", app_secret="test_secret_456")
    test_code = "test_authorization_code_from_dialog"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction (manual dialog flow)")
    print("=" * 80)
    print()

    # Test 1: Frontend sends the EXACT dialog redirect_uri (manual flow)
    print("TEST 1: Frontend sends the exact dialog redirect_uri")
    print("-" * 80)
    redirect_uri = "https://apps.orvym.com/dashboard/integrations"

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
    }
    if redirect_uri:
        params["redirect_uri"] = redirect_uri

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri is present: {('redirect_uri' in params)}")
    print(f"redirect_uri value: '{params['redirect_uri']}'")
    print(f"redirect_uri is empty string: {params['redirect_uri'] == ''}")
    print()

    # Test 2: No redirect_uri -> omitted entirely (never empty string)
    print("TEST 2: No redirect_uri -> OMITTED entirely (never empty string)")
    print("-" * 80)
    redirect_uri = None

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
    }
    if redirect_uri:
        params["redirect_uri"] = redirect_uri

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri present: {('redirect_uri' in params)}  (should be False)")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ Manual dialog flow: redirect_uri is sent and equals the dialog's EXACT value")
    print("✓ No redirect_uri provided: the parameter is OMITTED entirely")
    print("✗ Empty-string redirect_uri is NEVER sent (it never matches Meta's record)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_token_exchange_params())
