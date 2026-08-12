"""
Test Official Meta Embedded Signup Implementation

This test verifies that the token exchange follows Meta's official documentation:
- Only client_id, client_secret, and code parameters are sent
- redirect_uri is OMITTED entirely
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.meta_oauth import MetaOAuthService


class TestOfficialMetaImplementation:
    """Test suite for official Meta Embedded Signup implementation."""

    @pytest.mark.asyncio
    async def test_token_exchange_omits_redirect_uri(self):
        """Verify that token exchange omits redirect_uri parameter."""
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

            # CRITICAL VERIFICATION: redirect_uri must NOT be in params
            assert 'redirect_uri' not in params, "redirect_uri should be OMITTED per official Meta docs"

            # Verify only the three required parameters are present
            assert 'client_id' in params
            assert 'client_secret' in params
            assert 'code' in params
            assert len(params) == 3, "Only 3 parameters should be sent: client_id, client_secret, code"

            # Verify correct values
            assert params['client_id'] == "3862862217342382"
            assert params['code'] == test_code

            print("[PASS] Token exchange correctly omits redirect_uri")
            print(f"[PASS] Parameters sent: {list(params.keys())}")
            print("[PASS] Official Meta implementation verified")

    @pytest.mark.asyncio
    async def test_token_exchange_success(self):
        """Test successful token exchange with official implementation."""
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

    print("Test 1: Verify redirect_uri is omitted")
    print("-" * 80)
    asyncio.run(test.test_token_exchange_omits_redirect_uri())
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
    print("ALL TESTS PASSED - OFFICIAL META IMPLEMENTATION VERIFIED")
    print("=" * 80)
