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

IMPORTANT - How the WABA ID is identified (phone_numbers edge):

The access token obtained from Embedded Signup is a customer-scoped business
token. GET /me returns the TOKEN OWNER (business / system user), NOT the
WhatsApp Business Account (WABA). Calling /<owner_id>/phone_numbers therefore
fails with:
    (#100) Tried accessing nonexisting field (phone_numbers)
because phone_numbers is an EDGE of the WhatsAppBusinessAccount node, not a
field of a Business node.

Per Meta's WhatsApp Embedded Signup docs ("Manage accounts > Get shared WABA
ID with access token") the correct way to identify the WABA ID from the token
is the Debug Token endpoint:

    GET /debug_token?input_token=<SIGNUP_TOKEN>&access_token=<APP_ACCESS_TOKEN>

The response's data.granular_scopes entry for whatsapp_business_management
lists the WABA IDs the token was granted access to (most recently onboarded
first). Those WABA IDs are then queried through the WABA phone_numbers EDGE:

    GET /<WABA_ID>/phone_numbers?access_token=<BUSINESS_TOKEN>
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Prevent httpx/httpcore from logging the full request URL (which would expose
# the app secret and the full authorization code in the query string).
for _lib in ("httpx", "httpcore"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

# Params that must NEVER be logged in plaintext (tokens, secrets, codes).
_REDACTED_PARAMS = ("access_token", "input_token", "appsecret_proof",
                    "client_secret", "code")


class MetaOAuthService:
    """Service for handling Meta OAuth flow for WhatsApp Business API."""

    GRAPH_API_BASE = "https://graph.facebook.com/v26.0"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    # ============================================================
    # Safe logging helpers
    # ============================================================

    def _safe_params(self, params: Dict) -> Dict:
        """Return params with tokens/secrets/codes redacted (safe to log)."""
        safe = {}
        for k, v in params.items():
            if k in _REDACTED_PARAMS:
                safe[k] = f"<{len(str(v))} chars, REDACTED>"
            else:
                safe[k] = v
        return safe

    def _log_graph_request(self, method: str, url: str, params: Dict) -> None:
        """Log the exact Graph API request being sent.

        Logs the endpoint, HTTP method, API version, object ID/edge and the
        fields parameter. NEVER logs access tokens, input tokens or secrets.
        """
        # Object ID / edge from the URL path (query string never contains
        # secrets here because httpx sends params separately).
        path = url.replace(self.GRAPH_API_BASE, "").strip("/")

        logger.info("=" * 80)
        logger.info("META GRAPH API REQUEST")
        logger.info("=" * 80)
        logger.info(f"  Graph API endpoint: {url}")
        logger.info(f"  HTTP method: {method}")
        logger.info(f"  API version: {self.GRAPH_API_BASE.rstrip('/').rsplit('/', 1)[-1]}")
        logger.info(f"  Object ID / edge: /{path}")
        logger.info(f"  Parameter names: {list(params.keys())}")
        logger.info(f"  Fields parameter: {params.get('fields', 'NOT SET')}")
        logger.info(f"  Safe parameters: {self._safe_params(params)}")
        logger.info("=" * 80)

    def _log_exchange_request(self, url: str, params: Dict) -> None:
        """Log the exact request being sent to Meta (never the app secret or full code)."""
        log_params = self._safe_params(params)
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

    # ============================================================
    # Step 1 - Exchange code for access token
    # ============================================================

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

    # ============================================================
    # Step 2 - Identify WABA ID(s) granted to the access token
    # ============================================================

    async def get_waba_ids_from_token(self, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Identify the WhatsApp Business Account (WABA) ID(s) granted to a token.

        Uses Meta's Debug Token endpoint as documented in WhatsApp Embedded
        Signup ("Manage accounts > Get shared WABA ID with access token"):

            GET /debug_token?input_token=<SIGNUP_TOKEN>&access_token=<APP_ACCESS_TOKEN>

        The response's data.granular_scopes entry for
        whatsapp_business_management / whatsapp_business_messaging lists the
        WABA IDs the token can access, most recently onboarded first.
        data.user_id is the business / system user the token belongs to.

        NOTE: GET /me is NOT used here - it returns the token owner, not the
        WABA. Using the /me id as a WABA id produces:
            (#100) Tried accessing nonexisting field (phone_numbers)

        Args:
            access_token: The business access token returned by the exchange.

        Returns:
            (success, {"waba_ids": [str, ...], "user_id": str|None}, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/debug_token"
            # Meta docs: "An app access token or an app developer's user access
            # token for the app associated with the input_token is required."
            # App access token format is <APP_ID>|<APP_SECRET>.
            app_access_token = f"{self.app_id}|{self.app_secret}"
            params = {
                "input_token": access_token,
                "access_token": app_access_token,
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, error_obj = self._parse_error(response)
                logger.error(f"Debug token failed: {last_error} (code: {error_obj.get('code')})")
                return False, None, last_error or "Failed to inspect access token"

            data = response.json().get("data", {})

            waba_ids: list = []
            for gs in data.get("granular_scopes") or []:
                scope = gs.get("scope")
                if scope in ("whatsapp_business_management", "whatsapp_business_messaging"):
                    for target_id in gs.get("target_ids") or []:
                        sid = str(target_id)
                        if sid not in waba_ids:
                            waba_ids.append(sid)

            user_id = data.get("user_id")

            logger.info(f"Debug token OK - granular scopes found, WABA IDs identified: {waba_ids}")

            if not waba_ids:
                logger.error("No WABA IDs found in debug_token granular_scopes")
                return False, None, "No WhatsApp Business Account found. Complete WhatsApp Business setup and try again."

            return True, {"waba_ids": waba_ids, "user_id": user_id}, None

        except httpx.TimeoutException:
            logger.error("Debug token request timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Debug token error: {e}", exc_info=True)
            return False, None, str(e)

    # ============================================================
    # Step 3 - Get WABA details (name)
    # ============================================================

    async def get_waba_details(self, waba_id: str, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get WhatsApp Business Account (WABA) details by querying the WABA node.

        The WABA is a WhatsAppBusinessAccount node. Fields available include
        id and name. This is a read on the node itself (GET /<WABA_ID>), NOT a
        phone_numbers field lookup.

        Returns:
            (success, waba_data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{waba_id}"
            params = {
                "access_token": access_token,
                "fields": "id,name",
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, _ = self._parse_error(response)
                logger.error(f"Get WABA details failed: {last_error}")
                return False, None, last_error or "Failed to get WhatsApp Business Account"

            data = response.json()
            return True, data, None

        except httpx.TimeoutException:
            logger.error("Get WABA details timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Get WABA details error: {e}")
            return False, None, str(e)

    # ============================================================
    # Step 4 - Get phone numbers from the WABA's phone_numbers EDGE
    # ============================================================

    async def get_phone_numbers(self, waba_id: str, access_token: str) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Get phone numbers associated with the WABA.

        phone_numbers is a CONNECTION/EDGE of the WhatsAppBusinessAccount node,
        so this calls:

            GET /<WABA_ID>/phone_numbers?access_token=<TOKEN>

        It must be called with the WABA ID (see get_waba_ids_from_token), never
        the business ID or /me id - querying /<wrong_id>/phone_numbers fails
        with (#100) Tried accessing nonexisting field (phone_numbers).

        Returns:
            (success, phone_numbers_list, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{waba_id}/phone_numbers"
            params = {
                "access_token": access_token
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, _ = self._parse_error(response)
                logger.error(f"Get phone numbers failed: {last_error}")
                return False, None, last_error or "Failed to get phone numbers"

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

    # ============================================================
    # Orchestration - full Embedded Signup setup
    # ============================================================

    async def setup_whatsapp_integration(self, code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Complete WhatsApp integration setup from authorization code.

        This method orchestrates the full OAuth flow:
        1. Exchange code for access token
        2. Identify WABA ID via the Debug Token endpoint (granular_scopes)
        3. Get WABA details (name)
        4. Get phone numbers from the WABA's phone_numbers edge
        5. Return integration data (phone number ID, WABA ID, business ID)

        Args:
            code: Authorization code from Meta OAuth
            redirect_uri: The EXACT redirect_uri used in the OAuth dialog request
                (manual dialog flow). For the JS SDK / FB.login flow, pass None
                so redirect_uri is omitted from the exchange - never empty string.

        Returns:
            (success, integration_data, error_message)

        integration_data contains:
        - access_token: Long-lived access token
        - business_id: Meta business / system user ID (from debug_token user_id)
        - waba_id: WhatsApp Business Account ID (from debug_token granular_scopes)
        - business_name: WABA name
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

            # Step 2: Identify WABA ID(s) from the token (Debug Token endpoint)
            success, token_info, error = await self.get_waba_ids_from_token(access_token)
            if not success:
                logger.error(f"Step 2 failed - WABA identification: {error}")
                return False, None, error or "Failed to identify WhatsApp Business Account"

            waba_ids = token_info.get("waba_ids") or []
            waba_id = waba_ids[0]
            business_id = token_info.get("user_id") or waba_id
            logger.info(f"WABA ID identified: {waba_id} (business/system user ID: {business_id})")

            # Step 3: Get WABA details (name). Non-fatal if it fails.
            business_name = ""
            success, waba_data, error = await self.get_waba_details(waba_id, access_token)
            if success:
                business_name = waba_data.get("name", "")
                logger.info(f"WABA name: {business_name}")
            else:
                logger.warning(f"Could not fetch WABA name (continuing): {error}")

            # Step 4: Get phone numbers from the WABA's phone_numbers EDGE
            success, phone_numbers, error = await self.get_phone_numbers(waba_id, access_token)
            if not success:
                logger.error(f"Step 4 failed - Phone numbers: {error}")
                return False, None, error or "Failed to retrieve phone numbers"

            # Use the first phone number
            phone_data = phone_numbers[0]
            phone_number_id = phone_data.get("id")
            display_phone_number = phone_data.get("display_phone_number", "")

            integration_data = {
                "access_token": access_token,
                "business_id": business_id,
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
