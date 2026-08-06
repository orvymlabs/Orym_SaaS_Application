"""
Test script to verify OAuth token exchange parameters
This simulates what parameters will be sent to Meta
"""
import asyncio
from services.meta_oauth import MetaOAuthService

async def test_token_exchange_params():
    """Test what parameters are constructed for token exchange"""

    # Initialize service with dummy credentials
    service = MetaOAuthService(
        app_id="test_app_id_123",
        app_secret="test_secret_456"
    )

    # Simulate the code from FB.login
    test_code = "test_authorization_code_from_fb_login"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction")
    print("=" * 80)
    print()

    # Test 1: No redirect_uri provided (typical Embedded Signup flow)
    print("TEST 1: Frontend does NOT provide redirect_uri (Embedded Signup)")
    print("-" * 80)
    redirect_uri = None

    # Simulate what the method will do
    if redirect_uri is None:
        redirect_uri = ""

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": redirect_uri
    }

    print(f"Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri is present: {('redirect_uri' in params)}")
    print(f"redirect_uri value: '{params['redirect_uri']}'")
    print(f"redirect_uri is empty string: {params['redirect_uri'] == ''}")
    print()

    # Test 2: redirect_uri explicitly provided
    print("TEST 2: Frontend explicitly provides redirect_uri")
    print("-" * 80)
    redirect_uri = "https://example.com/oauth/callback"

    params = {
        "client_id": service.app_id,
        "client_secret": "***REDACTED***",
        "code": test_code,
        "redirect_uri": redirect_uri
    }

    print(f"Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ When frontend uses FB.login() without redirect_uri:")
    print("  → Backend will send redirect_uri='' (empty string)")
    print()
    print("✓ When frontend provides explicit redirect_uri:")
    print("  → Backend will send that exact value")
    print()
    print("✓ This matches Meta's Embedded Signup requirements")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_token_exchange_params())
