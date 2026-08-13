"""
Test Embedded Signup Token Exchange Parameters

This test verifies the token exchange for the FB.login() + config_id Embedded
Signup popup flow:
- client_id, client_secret, code and redirect_uri are sent, where redirect_uri
  is the EXACT value the JS SDK used in the OAuth dialog (the xd_arbiter
  channel URL - https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46).
  Sending a different redirect_uri as '' or any other URL triggers Meta error
  subcode 36008.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.meta_oauth import MetaOAuthService, EXCHANGE_REDIRECT_URI

EXPECTED_EXCHANGE_REDIRECT_URI = "https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46"


class TestOfficialMetaImplementation:
    """Test suite for official Meta Embedded Signup implementation."""

    @pytest.mark.asyncio
    async def test_token_exchange_sends_exact_dialog_redirect_uri(self):
        """Verify that token exchange sends redirect_uri = the exact JS SDK dialog value."""
        service = MetaOAuthService(
            app_id="3862862217342382",
            app_secret="test_secret"
        )

        test_code = "AQD" + "x" * 448  # Mock 451-character code

        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token",
                "token_type": "bearer"
            }

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Execute token exchange
            success, data, error = await service.exchange_code_for_token(test_code)

            # Verify the request was made
            assert mock_context.__aenter__.return_value.get.called
            call_args = mock_context.__aenter__.return_value.get.call_args

            # Get the params that were sent
            params = call_args[1]['params']

            # CRITICAL VERIFICATION: redirect_uri MUST be present and equal the
            # EXACT value the JS SDK used in the OAuth dialog (the xd_arbiter
            # channel URL - the value Meta binds to the code). Sending a
            # different redirect_uri (as empty string or real URL) triggers
            # error_subcode 36008.
            assert 'redirect_uri' in params, "redirect_uri must be present in the exchange for Embedded Signup flow"
            assert params['redirect_uri'] == EXPECTED_EXCHANGE_REDIRECT_URI
            assert EXCHANGE_REDIRECT_URI == EXPECTED_EXCHANGE_REDIRECT_URI

            # Verify the four parameters are present
            assert 'client_id' in params
            assert 'client_secret' in params
            assert 'code' in params
            assert len(params) == 4, f"Exactly 4 params: client_id, client_secret, code, redirect_uri, got {sorted(params.keys())}"

            # Verify correct values
            assert params['client_id'] == "3862862217342382"
            assert params['code'] == test_code

            print("[PASS] Token exchange sends redirect_uri = the exact JS SDK dialog value")
            print(f"[PASS] redirect_uri: {params['redirect_uri']}")
            print(f"[PASS] Parameters sent: {list(params.keys())}")
            print("[PASS] Embedded Signup popup exchange verified")

    @pytest.mark.asyncio
    async def test_token_exchange_success(self):
        """Test successful token exchange."""
        service = MetaOAuthService(
            app_id="3862862217342382",
            app_secret="test_secret"
        )

        test_code = "AQD" + "x" * 448

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "EAABwzLixnjYBO12345",
                "token_type": "bearer"
            }

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            success, data, error = await service.exchange_code_for_token(test_code)

            assert success is True
            assert data is not None
            assert data.get("access_token") == "EAABwzLixnjYBO12345"
            assert error is None

            print("[PASS] Token exchange succeeded with official implementation")

    @pytest.mark.asyncio
    async def test_token_exchange_handles_36008_error(self):
        """Test that 36008 error is handled correctly."""
        service = MetaOAuthService(
            app_id="3862862217342382",
            app_secret="test_secret"
        )

        test_code = "invalid_or_expired_code"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Error validating verification code"
            mock_response.json.return_value = {
                "error": {
                    "message": "Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request",
                    "type": "OAuthException",
                    "code": 100,
                    "error_subcode": 36008,
                    "fbtrace_id": "test123"
                }
            }

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            success, data, error = await service.exchange_code_for_token(test_code)

            assert success is False
            assert data is None
            assert "OAUTH_REDIRECT_URI_MISMATCH" in error
            assert "invalid, expired, or already consumed" in error

            print("[PASS] Error 36008 handled correctly")


if __name__ == "__main__":
    import asyncio

    print("=" * 80)
    print("TESTING OFFICIAL META EMBEDDED SIGNUP IMPLEMENTATION")
    print("=" * 80)
    print()

    test = TestOfficialMetaImplementation()

    print("Test 1: Verify the exact JS SDK dialog redirect_uri is sent")
    print("-" * 80)
    asyncio.run(test.test_token_exchange_sends_exact_dialog_redirect_uri())
    print()

    print("Test 2: Verify successful token exchange")
    print("-" * 80)
    asyncio.run(test.test_token_exchange_success())
    print()

    print("Test 3: Verify error 36008 handling")
    print("-" * 80)
    asyncio.run(test.test_token_exchange_handles_36008_error())
    print()

    print("=" * 80)
    print("ALL TESTS PASSED - EMBEDDED SIGNUP EXCHANGE VERIFIED")
    print("=" * 80)
