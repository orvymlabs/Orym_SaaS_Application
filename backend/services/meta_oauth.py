"""
Meta Embedded Signup OAuth Service
Handles WhatsApp Business API authentication via Meta Embedded Signup

IMPORTANT - How redirect_uri works in this flow:

The WhatsApp Embedded Signup is invoked through the OAuth dialog with
response_type=code + config_id. Meta binds the returned authorization code to
the exact redirect_uri used in that dialog request. The code exchange
(GET /oauth/access_token) therefore:

- MUST send redirect_uri = the EXACT value used in the dialog when the dialog
  was invoked manually (frontend-built dialog URL). Meta's "Manually Build a
  Login Flow" documentation states redirect_uri is required and must be
  identical to the one used in the OAuth dialog request.
- MUST OMIT redirect_uri entirely (never send an empty string) when the flow
  was invoked via FB.login() / the JS SDK, which per Meta's Facebook Login for
  Business and WhatsApp Embedded Signup documentation exchanges the code with
  only client_id + client_secret + code.

NEVER send redirect_uri="" (empty string). An empty-string redirect_uri is not
identical to any value Meta recorded in the dialog and triggers:
    "Error validating verification code. Please make sure your redirect_uri is
     identical to the one you used in the OAuth dialog request"
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Prevent httpx/httpcore from logging the full request URL (which would expose
# the app secret and the full authorization code in the query string).
for _lib in ("httpx", "httpcore"):
    logging.getLogger(_lib).setLevel(logging.WARNING)


class MetaOAuthService:
    """Service for handling Meta OAuth flow for WhatsApp Business API."""

    GRAPH_API_BASE = "https://graph.facebook.com/v26.0"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    def _log_exchange_request(self, url: str, params: Dict) -> None:
        """Log the exact request being sent to Meta (never the app secret or full code)."""
        log_params = {}
        for k, v in params.items():
            if k == "client_secret":
                log_params[k] = "***REDACTED***"
            elif k == "code":
                log_params[k] = f"<{len(v)} chars>"
            elif k == "redirect_uri":
                log_params[k] = repr(v)  # visible: the exact URI (never empty string)
            else:
                log_params[k] = v

        logger.info("=" * 80)
        logger.info("META OAUTH TOKEN EXCHANGE")
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

    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange authorization code for access token.

        The authorization code is bound by Meta to the exact redirect_uri used in
        the OAuth dialog request. This method therefore sends redirect_uri ONLY
        when the caller supplies the EXACT dialog redirect_uri (the manual
        dialog flow: frontend builds the dialog URL with a redirect_uri we
        control). When no redirect_uri is supplied (JS-SDK / FB.login flow) it
        is OMITTED entirely - never sent as an empty string.

        Per Meta's "Manually Build a Login Flow" documentation:
            redirect_uri is required and must be the same as the original
            redirect_uri used when starting the OAuth login process.

        Per Meta's Facebook Login for Business / WhatsApp Embedded Signup docs
        (JS SDK + config_id flow):
            GET /oauth/access_token?client_id&client_secret&code  (no redirect_uri)

        Args:
            code: Authorization code from Meta OAuth
            redirect_uri: The EXACT redirect_uri from the OAuth dialog request.
                If None/empty, redirect_uri is omitted from the exchange.

        Returns:
            (success, data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/oauth/access_token"

            params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
            }
            # Only include redirect_uri when the caller supplies the EXACT value
            # used in the dialog. Never send an empty string.
            if redirect_uri:
                params["redirect_uri"] = redirect_uri

            self._log_exchange_request(url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            self._log_exchange_response(response)

            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    logger.info("✅ Token exchange successful")
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
            redirect_uri: The EXACT redirect_uri used in the OAuth dialog request
                (manual dialog flow). For the JS SDK / FB.login flow, pass None
                so redirect_uri is omitted from the exchange - never empty string.

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
