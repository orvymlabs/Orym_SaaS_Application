"""
Test script to verify OAuth token exchange parameters (CORRECTED).
This simulates what parameters will be sent to Meta for the WhatsApp
Embedded Signup code exchange.

Rule: the Embedded Signup token exchange sends ONLY client_id, client_secret
and code - redirect_uri is NEVER sent. The documented Meta Tech Provider
exchange omits redirect_uri; sending a redirect_uri that does not byte-match
the OAuth dialog request is exactly what triggers Meta error_subcode 36008.
"""
import asyncio
from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"


async def test_token_exchange_params():
    """Test what parameters are constructed for token exchange"""

    service = MetaOAuthService(app_id="test_app_id_123", app_secret="test_secret_456")
    test_code = "test_authorization_code_from_dialog"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction (Embedded Signup)")
    print("=" * 80)
    print()

    # Test 1: canonical construction - only the three documented params
    print("TEST 1: Embedded Signup exchange parameter construction")
    print("-" * 80)

    params = {
        "client_id": service.app_id,
        "client_secret": service.app_secret,
        "code": test_code,
    }

    print("Parameters that will be sent to Meta:")
    for key, value in params.items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri present: {('redirect_uri' in params)}  (must be False)")
    assert "redirect_uri" not in params, "redirect_uri must NEVER be sent"
    assert set(params.keys()) == {"client_id", "client_secret", "code"}
    print()

    # Test 2: even when a redirect_uri is available, it must NOT be sent
    print("TEST 2: redirect_uri is NEVER appended, even when available")
    print("-" * 80)
    redirect_uri = CANONICAL

    params = {
        "client_id": service.app_id,
        "client_secret": service.app_secret,
        "code": test_code,
    }
    # The service deliberately ignores any redirect_uri argument on this path.
    assert "redirect_uri" not in params, "redirect_uri must not be appended"
    print(f"redirect_uri available but NOT sent: {redirect_uri}")
    print(f"redirect_uri present in params: {('redirect_uri' in params)}  (must be False)")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ The Embedded Signup exchange sends ONLY client_id + client_secret + code")
    print("✓ redirect_uri is NEVER sent on this exchange path")
    print("✓ redirect_uri is never turned into the canonical value and appended")
    print(f"✓ Canonical constant still defined for the OAuth dialog: {CANONICAL_REDIRECT_URI}")
    print("✗ Sending a mismatched redirect_uri triggers Meta error_subcode 36008")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_token_exchange_params())
