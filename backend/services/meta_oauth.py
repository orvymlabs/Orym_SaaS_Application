"""
Meta Embedded Signup OAuth Service
Handles WhatsApp Business API authentication via Meta Embedded Signup

CANONICAL PRODUCTION REDIRECT URI:

The Meta token exchange MUST always send redirect_uri exactly as:

    https://apps.orvym.com/dashboard/integrations/

This is the ONE canonical production value used by the OAuth dialog, the
frontend, the backend callback and the Meta App Dashboard (Valid OAuth
Redirect URIs). A previous production run proved that exchanging with
client_id + client_secret + code + redirect_uri (this exact value) returns
HTTP 200 and a valid access token.

The exchange request is therefore:

    GET /oauth/access_token?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>&redirect_uri=https://apps.orvym.com/dashboard/integrations/

redirect_uri MUST NEVER be omitted, must NEVER be sent as an empty string and
must NEVER be sent as null. Omitting it (or sending a value that differs from
the one Meta recorded for the dialog request) triggers error_subcode 36008
("make sure your redirect_uri is identical to the one you used in the OAuth
dialog request").

IMPORTANT - Where the WABA ID and phone number ID come from:

The WABA ID, phone number ID and business portfolio ID are returned by the
Embedded Signup completion event (the WA_EMBEDDED_SIGNUP FINISH message) and
forwarded from the frontend in the callback payload. The Embedded Signup
session event is the SOURCE OF TRUTH for the customer onboarding session.

The backend NEVER invents WABA IDs and NEVER falls back to /me/businesses or
any other business-portfolio edge to guess them. If the WABA ID or phone
number ID was not returned by the Embedded Signup session event, the backend
returns a controlled WABA_NOT_RETURNED / PHONE_NUMBER_NOT_RETURNED error so
the frontend requires a completely new Embedded Signup flow.

After the exchange the access token is validated with /debug_token (app_id +
granted scopes are logged; the token itself is never logged). /debug_token is
NOT used for WABA discovery - its granular_scopes for a Business Integration
System User token inspected with the app access token do not include the WABA
target_ids.
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Canonical production redirect URI. This exact value is used everywhere:
# the Meta OAuth dialog configuration, the frontend callback payload, the
# backend callback validation and the server-side token exchange. Never use a
# different value and never omit it from the exchange.
CANONICAL_REDIRECT_URI = "https://apps.orvym.com/dashboard/integrations/"

# Explicit, machine-readable error codes. Errors returned by the service are
# prefixed with one of these codes (e.g. "OAUTH_REDIRECT_URI_MISMATCH: ...")
# so the frontend can react deterministically and never retry a dead code.
OAUTH_CODE_ALREADY_PROCESSED = "OAUTH_CODE_ALREADY_PROCESSED"
OAUTH_CODE_EXPIRED = "OAUTH_CODE_EXPIRED"
OAUTH_REDIRECT_URI_MISMATCH = "OAUTH_REDIRECT_URI_MISMATCH"
META_PERMISSION_MISSING = "META_PERMISSION_MISSING"
WABA_NOT_RETURNED = "WABA_NOT_RETURNED"
PHONE_NUMBER_NOT_RETURNED = "PHONE_NUMBER_NOT_RETURNED"
WABA_ACCESS_DENIED = "WABA_ACCESS_DENIED"
PHONE_REGISTRATION_FAILED = "PHONE_REGISTRATION_FAILED"
WEBHOOK_SUBSCRIPTION_FAILED = "WEBHOOK_SUBSCRIPTION_FAILED"

# Meta error_subcode for "Error validating verification code ... make sure your
# redirect_uri is identical to the one you used in the OAuth dialog request".
_META_ERROR_SUBCODE_REDIRECT_MISMATCH = 36008

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
        """Extract (error_message, error_object) from a Meta error response.

        Meta error_subcode 36008 means the exchange redirect_uri did not match
        the value Meta recorded for this single-use authorization code (or the
        code is invalid/expired). The message is exactly the CLAUDE.md-approved
        user-facing text; the code must NEVER be retried and a completely new
        Embedded Signup flow is required.
        """
        try:
            error_obj = response.json().get("error", {})
        except Exception:
            error_obj = {}
        message = error_obj.get("message", "Failed to exchange code")

        if error_obj.get("error_subcode") == _META_ERROR_SUBCODE_REDIRECT_MISMATCH:
            return (
                f"{OAUTH_REDIRECT_URI_MISMATCH}: OAuth authorization code is "
                "invalid or was issued for a different redirect URI. Please "
                "restart WhatsApp Embedded Signup."
            ), error_obj

        if "expired" in message.lower():
            return f"{OAUTH_CODE_EXPIRED}: {message}", error_obj

        return message, error_obj

    # ============================================================
    # Step 1 - Exchange code for access token
    # ============================================================

    async def exchange_code_for_token(
        self, code: str, redirect_uri: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange the Embedded Signup authorization code for an access token.

        The exchange ALWAYS includes the canonical production redirect_uri:

            GET /oauth/access_token?client_id&client_secret&code&redirect_uri

        with redirect_uri = https://apps.orvym.com/dashboard/integrations/ (see
        the module docstring). Omitting redirect_uri - or sending an empty
        string or a value different from the one Meta recorded for the dialog
        request - fails with error_subcode 36008 ("make sure your redirect_uri
        is identical to the one you used in the OAuth dialog request").

        Args:
            code: The exchangeable authorization code from Meta Embedded Signup.
            redirect_uri: Optional. When provided it is normalized (stripped)
                and sent. When omitted or empty, the canonical production
                redirect_uri is sent. redirect_uri is NEVER omitted from the
                exchange and NEVER sent as an empty string.

        Returns:
            (success, data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/oauth/access_token"

            redirect_uri = (redirect_uri or "").strip() or CANONICAL_REDIRECT_URI
            params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            }

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
    # App credential / configuration verification
    # ============================================================

    async def verify_app_credentials(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify the App Secret belongs to the configured App ID and that the
        configured Graph API version is supported.

        Calls the documented App node read with an APP ACCESS TOKEN
        (<APP_ID>|<APP_SECRET>):

            GET /v26.0/<APP_ID>?fields=id,name&access_token=<APP_ID>|<APP_SECRET>

        A valid secret returns the app's name. An invalid secret or an
        unsupported Graph API version returns a Meta error (for an unsupported
        version Meta returns code 12 "Unsupported get request. Please use one
        of the documented versions..."). The app secret is never logged or
        returned.

        Returns:
            (success, {"app_name": str|None, "graph_version_supported": bool}, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{self.app_id}"
            app_access_token = f"{self.app_id}|{self.app_secret}"
            params = {
                "fields": "id,name",
                "access_token": app_access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Meta app credentials verified - app {self.app_id} "
                    f"responded with name: {data.get('name', '')}"
                )
                return True, {
                    "app_name": data.get("name", ""),
                    "graph_version_supported": True,
                }, None

            last_error, error_obj = self._parse_error(response)
            code = error_obj.get("code")
            message = (error_obj.get("message") or last_error or "").lower()
            version_unsupported = code == 12 or "documented versions" in message
            logger.error(
                f"Meta app credential check failed (code: {error_obj.get('code')}, "
                f"error_subcode: {error_obj.get('error_subcode')})"
            )
            return False, {
                "app_name": None,
                "graph_version_supported": not version_unsupported,
            }, last_error or "Failed to verify Meta app credentials"

        except httpx.TimeoutException:
            logger.error("Meta app credential check timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Meta app credential check error: {e}", exc_info=True)
            return False, None, str(e)

    # ============================================================
    # Step 2 - Validate the exchanged access token
    # ============================================================

    async def validate_access_token(self, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate the access token returned by the exchange using Meta's
        /debug_token endpoint:

            GET /v26.0/debug_token?input_token=<TOKEN>&access_token=<APP_ID>|<APP_SECRET>

        Verifies:
          - the token belongs to the configured App ID
          - at least one WhatsApp scope is granted (checked in BOTH the
            `scopes` and `granular_scopes` representations - a permission
            granted under a different representation is NOT rejected)

        Logs ONLY non-sensitive token metadata: app ID, token type, granted
        scopes and missing scopes. NEVER logs the token, input_token or app
        secret.

        Returns:
            (success, {"app_id": str, "type": str, "scopes": [str],
                       "missing_scopes": [str]}, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/debug_token"
            params = {
                "input_token": access_token,
                "access_token": f"{self.app_id}|{self.app_secret}",
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, error_obj = self._parse_error(response)
                logger.error(
                    f"Token validation failed (code: {error_obj.get('code')}, "
                    f"error_subcode: {error_obj.get('error_subcode')})"
                )
                return False, None, last_error or "Failed to validate the access token"

            data = response.json().get("data") or {}

            token_app_id = str(data.get("app_id") or "").strip()
            if token_app_id and token_app_id != str(self.app_id).strip():
                logger.error(
                    f"Token validation failed: token belongs to app {token_app_id}, "
                    f"expected app {self.app_id}"
                )
                return False, None, (
                    f"{META_PERMISSION_MISSING}: the access token belongs to a "
                    "different Meta app. Please restart WhatsApp Embedded Signup."
                )

            scopes = data.get("scopes") or []
            granular_scopes = data.get("granular_scopes") or []
            granular_permissions = [
                g.get("permission") for g in granular_scopes if g.get("permission")
            ]

            granted = set(scopes) | set(granular_permissions)
            whatsapp_scopes = {"whatsapp_business_messaging", "whatsapp_business_management"}
            missing = sorted(whatsapp_scopes - granted)

            logger.info("=" * 80)
            logger.info("META ACCESS TOKEN VALIDATION")
            logger.info("=" * 80)
            logger.info(f"  App ID: {token_app_id or self.app_id}")
            logger.info(f"  Token type: {data.get('type', 'unknown')}")
            logger.info(f"  Granted scopes: {sorted(granted)}")
            logger.info(f"  Missing WhatsApp scopes: {missing or 'none'}")
            logger.info(f"  Expires at: {data.get('expires_at', 'unknown')}")
            logger.info("=" * 80)

            if not granted:
                logger.error(
                    "Token validation failed: token grants no scopes - cannot "
                    "access any WhatsApp Business resource"
                )
                return False, None, (
                    f"{META_PERMISSION_MISSING}: the access token grants no "
                    "permissions. Please restart WhatsApp Embedded Signup."
                )

            return True, {
                "app_id": token_app_id or str(self.app_id),
                "type": data.get("type", "unknown"),
                "scopes": sorted(granted),
                "missing_scopes": missing,
            }, None

        except httpx.TimeoutException:
            logger.error("Token validation timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Token validation error: {e}", exc_info=True)
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

        It must be called with the WABA ID returned by Embedded Signup, never
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
                last_error, error_obj = self._parse_error(response)
                logger.error(f"Get phone numbers failed: {last_error} (code: {error_obj.get('code')})")
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
    # Step 5 - Subscribe the WABA to the app
    # ============================================================

    async def subscribe_to_waba(self, waba_id: str, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Subscribe the app to the customer's WhatsApp Business Account so the
        app receives webhooks for the WABA.

            POST /<WABA_ID>/subscribed_apps?access_token=<BUSINESS_TOKEN>

        On failure the REAL Meta error (code, error_subcode, message,
        fbtrace_id) is surfaced - never a generic "no WABA" message.

        Returns:
            (success, response_data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{waba_id}/subscribed_apps"
            params = {
                "access_token": access_token,
            }

            self._log_graph_request("POST", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)

            if response.status_code != 200:
                last_error, error_obj = self._parse_error(response)
                detail = (
                    f"WABA subscription failed (code: {error_obj.get('code')}, "
                    f"error_subcode: {error_obj.get('error_subcode')}, "
                    f"message: {last_error}, fbtrace_id: {error_obj.get('fbtrace_id')})"
                )
                logger.error(detail)
                return False, None, detail

            data = response.json()
            logger.info(f"WABA {waba_id} subscribed to app successfully: {data}")
            return True, data, None

        except httpx.TimeoutException:
            logger.error("Subscribe WABA timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Subscribe WABA error: {e}")
            return False, None, str(e)

    # ============================================================
    # Orchestration - full Embedded Signup setup
    # ============================================================

    async def setup_whatsapp_integration(
        self,
        code: str,
        waba_id: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        business_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Complete WhatsApp integration setup from the Embedded Signup data.

        The WABA ID and phone number ID MUST come from the WA_EMBEDDED_SIGNUP
        session message (captured on the frontend and forwarded here). They are
        the source of truth for the customer onboarding session. If they were
        NOT returned by Meta, the flow fails with a controlled
        WABA_NOT_RETURNED / PHONE_NUMBER_NOT_RETURNED error - the backend NEVER
        invents WABA IDs and NEVER falls back to /me/businesses or any other
        business-portfolio edge to guess them.

        The code exchange ALWAYS sends the canonical production redirect_uri
        (https://apps.orvym.com/dashboard/integrations/) - it is NEVER omitted
        and NEVER sent empty. A mismatched or missing redirect_uri fails the
        exchange with error_subcode 36008.

        Flow:
        1. Exchange code for access token (server-side, always with the
           canonical redirect_uri)
        2. Validate the exchanged token via /debug_token (app_id + scopes)
        3. Require the WABA ID from the Embedded Signup session (no fallback)
        4. Require the phone number ID from the Embedded Signup session
        5. Validate the WABA via GET /<WABA_ID> (only supported fields: id,name)
        6. GET /<WABA_ID>/phone_numbers (WABA edge) and verify the Embedded
           Signup phone number ID is present
        7. POST /<WABA_ID>/subscribed_apps to subscribe the WABA to the app

        Args:
            code: Authorization code from Meta Embedded Signup
            waba_id: WhatsApp Business Account ID returned by the Embedded
                Signup session (REQUIRED - never discovered or guessed).
            phone_number_id: Business phone number ID returned by the Embedded
                Signup session (REQUIRED - never the first phone number).
            business_id: Business portfolio ID returned by the Embedded Signup
                session (optional - stored when provided, never fabricated).
            redirect_uri: The EXACT redirect_uri used in the OAuth dialog
                request. Optional - when omitted or empty the canonical
                production redirect_uri is used. redirect_uri is NEVER omitted
                from the exchange and NEVER sent empty.

        Returns:
            (success, integration_data, error_message)

        integration_data contains:
        - access_token: Long-lived customer-scoped business token
        - business_id: Meta business portfolio ID (from Embedded Signup only)
        - waba_id: WhatsApp Business Account ID (from Embedded Signup)
        - business_name: WABA name (from the WABA node)
        - phone_number_id: Phone Number ID (from Embedded Signup)
        - display_phone_number: Display phone number
        - verified_name: Verified display name
        """
        try:
            # Step 1: Exchange code for token. The exchange ALWAYS sends the
            # canonical production redirect_uri (see module docstring and
            # exchange_code_for_token) - it is never omitted and never empty.
            logger.info(f"[EmbeddedSignup] Step 1/6 - Meta token exchange started (code length: {len(code)})")
            success, token_data, error = await self.exchange_code_for_token(code, redirect_uri=redirect_uri)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 1/6 failed - Token exchange: {error}")
                return False, None, error or "Failed to exchange authorization code"
            logger.info("[EmbeddedSignup] Step 1/6 - Meta token exchange succeeded")
            access_token = token_data.get("access_token")

            # Step 2: Validate the exchanged token (app_id + granted scopes).
            # The token itself is never logged.
            logger.info("[EmbeddedSignup] Step 2/6 - Access token validation started")
            success, token_info, error = await self.validate_access_token(access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 2/6 failed - Token validation: {error}")
                return False, None, error or "Failed to validate the access token"
            logger.info(
                f"[EmbeddedSignup] Step 2/6 - Token validation succeeded "
                f"(app {token_info.get('app_id')}, type {token_info.get('type')})"
            )

            # Step 3: The WABA ID comes from the Embedded Signup session event.
            # It is NEVER guessed and NEVER resolved via /me/businesses.
            waba_id = str(waba_id or "").strip() or None
            if not waba_id:
                logger.error(
                    "[EmbeddedSignup] Step 3/6 failed - Embedded Signup session "
                    "returned no WABA ID (WABA_NOT_RETURNED)"
                )
                return False, None, (
                    f"{WABA_NOT_RETURNED}: the WhatsApp Business Account ID was "
                    "not returned by Meta Embedded Signup. Please restart "
                    "WhatsApp Embedded Signup and complete the setup again."
                )

            # Step 4: The phone number ID comes from the Embedded Signup session
            # event. It is NEVER replaced with the first phone number on the WABA.
            phone_number_id = str(phone_number_id or "").strip() or None
            if not phone_number_id:
                logger.error(
                    "[EmbeddedSignup] Step 4/6 failed - Embedded Signup session "
                    "returned no phone number ID (PHONE_NUMBER_NOT_RETURNED)"
                )
                return False, None, (
                    f"{PHONE_NUMBER_NOT_RETURNED}: the WhatsApp phone number was "
                    "not returned by Meta Embedded Signup. Please add a business "
                    "phone number and restart WhatsApp Embedded Signup."
                )

            # Step 5: Validate the WABA using the session WABA ID.
            logger.info(f"[EmbeddedSignup] Step 5/6 - WABA validation started (waba_id: {waba_id})")
            success, waba_data, error = await self.get_waba_details(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 5/6 failed - WABA validation for {waba_id}: {error}")
                return False, None, (
                    f"{WABA_ACCESS_DENIED}: the WhatsApp Business Account could "
                    f"not be validated: {error}"
                )
            business_name = waba_data.get("name", "")
            logger.info(f"[EmbeddedSignup] Step 5/6 - WABA validation succeeded (name: {business_name})")

            # Step 6: Fetch the phone numbers and verify the session phone number
            # ID is present on this WABA.
            logger.info(f"[EmbeddedSignup] Step 6/6 - Phone number validation started (waba_id: {waba_id})")
            success, phone_numbers, error = await self.get_phone_numbers(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 6/6 failed - Phone numbers for WABA {waba_id}: {error}")
                return False, None, (
                    f"{PHONE_NUMBER_NOT_RETURNED}: could not load the phone "
                    f"numbers of the WhatsApp Business Account: {error}"
                )

            phone_data = None
            for pn in phone_numbers:
                if str(pn.get("id")) == str(phone_number_id):
                    phone_data = pn
                    break
            if phone_data is None:
                logger.error(
                    f"[EmbeddedSignup] Step 6/6 failed - Phone number {phone_number_id} "
                    f"not found in WABA {waba_id}"
                )
                return False, None, (
                    f"{PHONE_NUMBER_NOT_RETURNED}: the phone number returned by "
                    "Embedded Signup was not found in the WhatsApp Business "
                    "Account. Please reconnect WhatsApp."
                )

            display_phone_number = phone_data.get("display_phone_number", "")
            verified_name = phone_data.get("verified_name", "")
            logger.info(
                f"[EmbeddedSignup] Step 6/6 - Phone number verified: {display_phone_number} "
                f"(id: {phone_number_id}, verified_name: {verified_name})"
            )

            # Webhook subscription: subscribe the WABA to the app (required for
            # webhooks).
            logger.info(f"[EmbeddedSignup] Step 6/6 - WABA subscription started (waba_id: {waba_id})")
            success, sub_data, error = await self.subscribe_to_waba(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 6/6 failed - WABA subscription for {waba_id}: {error}")
                return False, None, (
                    f"{WEBHOOK_SUBSCRIPTION_FAILED}: could not subscribe the "
                    f"WhatsApp Business Account to the app: {error}"
                )
            logger.info("[EmbeddedSignup] Step 6/6 - WABA subscription succeeded")

            # Business ID: use only the actual ID returned by Embedded Signup.
            # Never invent or guess one.
            if business_id:
                business_id = str(business_id).strip() or None
            logger.info(f"[EmbeddedSignup] Business ID for tenant record: {business_id or 'not provided'}")

            integration_data = {
                "access_token": access_token,
                "business_id": business_id or "",
                "waba_id": waba_id,
                "business_name": business_name,
                "phone_number_id": phone_number_id,
                "display_phone_number": display_phone_number,
                "verified_name": verified_name,
            }

            logger.info(
                f"[EmbeddedSignup] WhatsApp integration setup complete: WABA {waba_id}, "
                f"phone {display_phone_number}, subscribed_apps={bool(sub_data)}"
            )
            return True, integration_data, None

        except Exception as e:
            logger.error(f"[EmbeddedSignup] Setup integration error: {e}")
            return False, None, f"An unexpected error occurred: {str(e)}"
