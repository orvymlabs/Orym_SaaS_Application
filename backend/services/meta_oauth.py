"""
Meta Embedded Signup OAuth Service
Handles WhatsApp Business API authentication via Meta Embedded Signup

IMPORTANT: For Embedded Signup with FB.login() + config_id:
- Frontend calls FB.login({config_id, response_type: 'code'}) WITHOUT redirect_uri
- Meta returns authorization code via JavaScript callback
- Token exchange MUST include redirect_uri="" (empty string)
- This is different from standard OAuth which omits redirect_uri entirely
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MetaOAuthService:
    """Service for handling Meta OAuth flow for WhatsApp Business API."""

    GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Meta OAuth
            redirect_uri: Optional redirect URI (must match the one used in authorization if provided)

        Returns:
            (success, data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/oauth/access_token"

            # CRITICAL: For Embedded Signup with FB.login() and config_id,
            # the redirect_uri used by FB.login() internally must match the token exchange.
            # We'll try multiple possibilities to find the correct one.

            redirect_uris_to_try = []

            if redirect_uri:
                # If explicitly provided, try that first
                redirect_uris_to_try.append(redirect_uri)

            # Common redirect_uri values for FB.login() with Embedded Signup:
            redirect_uris_to_try.extend([
                "https://apps.orvym.com/dashboard/integrations",  # Frontend page URL
                "https://apps.orvym.com",  # Frontend base URL
                "",  # Empty string (some implementations use this)
                "https://www.facebook.com/connect/login_success.html",  # Facebook's default for SDK
            ])

            last_error_msg = None
            last_error_details = None

            for idx, uri in enumerate(redirect_uris_to_try):
                params = {
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "code": code,
                    "redirect_uri": uri
                }

                # Log the attempt
                log_params = {k: (v if k != "client_secret" else "***REDACTED***") for k, v in params.items()}
                logger.info("=" * 80)
                logger.info(f"META OAUTH TOKEN EXCHANGE - ATTEMPT {idx + 1}/{len(redirect_uris_to_try)}")
                logger.info("=" * 80)
                logger.info(f"  URL: {url}")
                logger.info(f"  Method: GET")
                logger.info(f"  Parameters: {log_params}")
                logger.info(f"  redirect_uri: '{uri}'")
                logger.info(f"  Code length: {len(code)}")
                logger.info("=" * 80)

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)

                    logger.info(f"META GRAPH API RESPONSE:")
                    logger.info(f"  Status Code: {response.status_code}")
                    logger.info(f"  Response Body (FULL): {response.text}")

                    if response.status_code == 200:
                        data = response.json()
                        access_token = data.get("access_token")

                        if access_token:
                            logger.info(f"✅ Token exchange successful with redirect_uri: '{uri}'")
                            return True, data, None
                        else:
                            logger.error(f"No access token in response: {data}")
                            last_error_msg = "No access token returned"
                            last_error_details = data
                    else:
                        # Failed attempt - log and try next
                        error_data = response.json() if response.text else {}
                        error_obj = error_data.get("error", {})
                        error_msg = error_obj.get("message", "Failed to exchange code")
                        error_code = error_obj.get("code", "unknown")
                        error_subcode = error_obj.get("error_subcode", "none")
                        fbtrace_id = error_obj.get("fbtrace_id", "none")

                        logger.warning(f"❌ ATTEMPT {idx + 1} FAILED")
                        logger.warning(f"  Error Code: {error_code}")
                        logger.warning(f"  Error Subcode: {error_subcode}")
                        logger.warning(f"  Error Message: {error_msg}")
                        logger.warning(f"  FB Trace ID: {fbtrace_id}")

                        last_error_msg = error_msg
                        last_error_details = error_obj

                        # If this was the last attempt, log full details
                        if idx == len(redirect_uris_to_try) - 1:
                            logger.error("=" * 80)
                            logger.error("ALL ATTEMPTS FAILED - FULL ERROR DETAILS")
                            logger.error("=" * 80)
                            logger.error(f"  Error Code: {error_code}")
                            logger.error(f"  Error Subcode: {error_subcode}")
                            logger.error(f"  Error Type: {error_obj.get('type', 'unknown')}")
                            logger.error(f"  Error Message: {error_msg}")
                            logger.error(f"  FB Trace ID: {fbtrace_id}")
                            logger.error(f"  Full Error Object: {error_obj}")
                            logger.error(f"  Full Response: {response.text}")
                            logger.error("=" * 80)

            # All attempts failed
            return False, None, last_error_msg or "Failed to exchange code with any redirect_uri"

        except httpx.TimeoutException:
            logger.error("Token exchange timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Token exchange error: {e}", exc_info=True)
            return False, None, str(e)

    async def get_whatsapp_business_account(self, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get WhatsApp Business Account details.

        Returns:
            (success, waba_data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/me"
            params = {
                "access_token": access_token,
                "fields": "id,name"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Failed to get business account")
                    logger.error(f"Get WABA failed: {error_msg}")
                    return False, None, error_msg

                data = response.json()
                return True, data, None

        except httpx.TimeoutException:
            logger.error("Get WABA timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Get WABA error: {e}")
            return False, None, str(e)

    async def get_phone_numbers(self, waba_id: str, access_token: str) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Get phone numbers associated with the WABA.

        Returns:
            (success, phone_numbers_list, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{waba_id}/phone_numbers"
            params = {
                "access_token": access_token
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Failed to get phone numbers")
                    logger.error(f"Get phone numbers failed: {error_msg}")
                    return False, None, error_msg

                data = response.json()
                phone_numbers = data.get("data", [])

                if not phone_numbers:
                    return False, None, "No phone numbers found in this WhatsApp Business Account"

                return True, phone_numbers, None

        except httpx.TimeoutException:
            logger.error("Get phone numbers timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Get phone numbers error: {e}")
            return False, None, str(e)

    async def setup_whatsapp_integration(self, code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Complete WhatsApp integration setup from authorization code.

        This method orchestrates the full OAuth flow:
        1. Exchange code for access token
        2. Get WhatsApp Business Account ID
        3. Get phone number details

        Args:
            code: Authorization code from Meta OAuth
            redirect_uri: Optional redirect URI (must match the one used in authorization)

        Returns:
            (success, integration_data, error_message)

        integration_data contains:
        - access_token: Long-lived access token
        - business_id: Meta Business ID
        - waba_id: WhatsApp Business Account ID
        - phone_number_id: Phone Number ID
        - display_phone_number: Display phone number
        """
        try:
            # Step 1: Exchange code for token
            logger.info(f"Starting WhatsApp integration setup (code length: {len(code)})")
            success, token_data, error = await self.exchange_code_for_token(code, redirect_uri)
            if not success:
                logger.error(f"Step 1 failed - Token exchange: {error}")
                return False, None, error or "Failed to exchange authorization code"

            access_token = token_data.get("access_token")

            # Step 2: Get Business Account details
            success, waba_data, error = await self.get_whatsapp_business_account(access_token)
            if not success:
                return False, None, error or "Failed to retrieve WhatsApp Business Account"

            waba_id = waba_data.get("id")
            business_name = waba_data.get("name", "")

            # Step 3: Get phone numbers
            success, phone_numbers, error = await self.get_phone_numbers(waba_id, access_token)
            if not success:
                return False, None, error or "Failed to retrieve phone numbers"

            # Use the first phone number
            phone_data = phone_numbers[0]
            phone_number_id = phone_data.get("id")
            display_phone_number = phone_data.get("display_phone_number", "")

            integration_data = {
                "access_token": access_token,
                "business_id": waba_id,
                "waba_id": waba_id,
                "business_name": business_name,
                "phone_number_id": phone_number_id,
                "display_phone_number": display_phone_number,
            }

            logger.info(f"Successfully setup WhatsApp integration for WABA {waba_id}, phone {display_phone_number}")
            return True, integration_data, None

        except Exception as e:
            logger.error(f"Setup integration error: {e}")
            return False, None, f"An unexpected error occurred: {str(e)}"
