"""
Meta Embedded Signup OAuth Service
Handles WhatsApp Business API authentication via Meta Embedded Signup

IMPORTANT: For Embedded Signup with FB.login() + config_id:
- Frontend calls FB.login({config_id, response_type: 'code', override_default_response_type: true})
  WITHOUT a redirect_uri. Meta returns the exchangeable code via the JavaScript callback.
- Meta's OAuth servers record the dialog's redirect_uri as an EMPTY STRING for this flow,
  so the token exchange must send redirect_uri="" (empty string).
- Omitting redirect_uri entirely (or sending a non-empty value) triggers:
    "Error validating verification code. Please make sure your redirect_uri is identical
     to the one you used in the OAuth dialog request"
- If Meta still rejects with redirect_uri=="" we retry omitting redirect_uri entirely
  (the variant shown in some Meta documentation).
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Prevent httpx/httpcore from logging the full request URL (which would expose
# the app secret and the full authorization code in the query string).
for _lib in ("httpx", "httpcore"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

REDIRECT_URI_ERROR_SUBCODES = (36001, 36008)


class MetaOAuthService:
    """Service for handling Meta OAuth flow for WhatsApp Business API."""

    GRAPH_API_BASE = "https://graph.facebook.com/v26.0"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    def _log_exchange_request(self, url: str, params: Dict, attempt: int, total: int) -> None:
        """Log the exact request being sent to Meta (never the app secret or full code)."""
        log_params = {}
        for k, v in params.items():
            if k == "client_secret":
                log_params[k] = "***REDACTED***"
            elif k == "code":
                log_params[k] = f"<{len(v)} chars>"
            elif k == "redirect_uri":
                log_params[k] = repr(v)  # visible: "", None, or the exact URI
            else:
                log_params[k] = v

        logger.info("=" * 80)
        logger.info(f"META OAUTH TOKEN EXCHANGE - Embedded Signup Flow (attempt {attempt}/{total})")
        logger.info("=" * 80)
        logger.info(f"  Meta endpoint: {url}")
        logger.info(f"  Method: GET")
        logger.info(f"  App ID: {self.app_id}")
        logger.info(f"  Parameter names: {list(params.keys())}")
        logger.info(f"  redirect_uri included: {'redirect_uri' in params}")
        logger.info(f"  redirect_uri value: {log_params.get('redirect_uri', 'OMITTED')}")
        logger.info(f"  Code length: {len(params.get('code', ''))}")
        logger.info("=" * 80)

    def _log_exchange_response(self, response: httpx.Response) -> None:
        """Log Meta's response (status, error code/subcode, fbtrace_id - never tokens)."""
        logger.info(f"META GRAPH API RESPONSE:")
        logger.info(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json() if response.text else {}
            logger.info(f"  Access token received: {'YES' if data.get('access_token') else 'NO'}")
        else:
            try:
                error_obj = response.json().get("error", {})
            except Exception:
                error_obj = {}
            logger.info(f"  Error code: {error_obj.get('code', 'unknown')}")
            logger.info(f"  Error subcode: {error_obj.get('error_subcode', 'none')}")
            logger.info(f"  Error type: {error_obj.get('type', 'unknown')}")
            logger.info(f"  Error message: {error_obj.get('message', response.text[:300])}")
            logger.info(f"  fbtrace_id: {error_obj.get('fbtrace_id', 'none')}")

    def _parse_error(self, response: httpx.Response) -> Tuple[str, Dict]:
        """Extract (error_message, error_object) from a Meta error response."""
        try:
            error_obj = response.json().get("error", {})
        except Exception:
            error_obj = {}
        message = error_obj.get("message", "Failed to exchange code")
        return message, error_obj

    def _is_redirect_uri_error(self, error_obj: Dict) -> bool:
        """True when Meta rejects the exchange because of redirect_uri validation."""
        message = (error_obj.get("message") or "").lower()
        subcode = error_obj.get("error_subcode")
        return "redirect_uri" in message or subcode in REDIRECT_URI_ERROR_SUBCODES

    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange authorization code for access token.

        Meta Embedded Signup (FB.login + config_id) returns the exchangeable code via
        the JavaScript callback and does NOT use a redirect_uri during authorization.
        Meta records the dialog redirect_uri as an EMPTY STRING for this flow, so the
        exchange must send redirect_uri="" (empty string).

        Strategy (most likely to succeed first):
          1. Send redirect_uri="" (empty string) - matches the JS SDK dialog.
          2. If Meta still rejects on redirect_uri, retry omitting it entirely.

        Args:
            code: Authorization code from Meta OAuth
            redirect_uri: Optional explicit redirect URI (used only if supplied)

        Returns:
            (success, data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/oauth/access_token"

            # Build candidate parameter sets (most likely to succeed first).
            if redirect_uri:
                candidate_params = [
                    {
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    }
                ]
            else:
                # Embedded Signup: empty-string redirect_uri first, omit as fallback.
                candidate_params = [
                    {
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "code": code,
                        "redirect_uri": "",
                    },
                    {
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "code": code,
                    },
                ]

            last_error = None
            total = len(candidate_params)

            for index, params in enumerate(candidate_params, start=1):
                self._log_exchange_request(url, params, attempt=index, total=total)

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)

                self._log_exchange_response(response)

                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")
                    if access_token:
                        logger.info(f"✅ Token exchange successful (redirect_uri: {params.get('redirect_uri', 'OMITTED')})")
                        return True, data, None
                    logger.error(f"No access token in response: {data}")
                    return False, None, "No access token returned"

                last_error, error_obj = self._parse_error(response)

                logger.error("=" * 80)
                logger.error("META GRAPH API ERROR - FULL DETAILS")
                logger.error("=" * 80)
                logger.error(f"  Error Code: {error_obj.get('code', 'unknown')}")
                logger.error(f"  Error Subcode: {error_obj.get('error_subcode', 'none')}")
                logger.error(f"  Error Type: {error_obj.get('type', 'unknown')}")
                logger.error(f"  Error Message: {error_obj.get('message', '')}")
                logger.error(f"  FB Trace ID: {error_obj.get('fbtrace_id', 'none')}")
                logger.error("=" * 80)

                # Only retry when the failure is a redirect_uri validation issue.
                if not self._is_redirect_uri_error(error_obj):
                    return False, None, last_error

            return False, None, last_error or "Failed to exchange code"

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
            redirect_uri: Optional redirect URI. For Embedded Signup (FB.login +
                config_id) Meta records the dialog's redirect_uri as an empty string,
                so the exchange sends redirect_uri="" (empty string) automatically.

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
