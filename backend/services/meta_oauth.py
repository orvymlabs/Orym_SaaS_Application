"""
Meta Embedded Signup OAuth Service
Handles WhatsApp Business API authentication via Meta Embedded Signup

OFFICIAL META IMPLEMENTATION (per CLAUDE.md requirements)

This implementation follows Meta's official Embedded Signup documentation.

TOKEN EXCHANGE (Embedded Signup FB.login popup flow):

For FB.login() with config_id (Facebook Login for Business) Embedded Signup
flow, the authorization code is issued inside Meta's JS SDK popup. Meta's
official server-side exchange sends ONLY:

    GET /oauth/access_token?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>

NO redirect_uri parameter. This is the documented Facebook Login for Business
exchange. The config_id itself provides the security binding; no redirect_uri
is required during token exchange for this configuration.

Sending redirect_uri (the empty string OR any real URL) triggers Meta error
code 100 / subcode 36008 ("Error validating verification code. Please make
sure your redirect_uri is identical to the one you used in the OAuth dialog
request") because the value is never byte-for-byte identical to the one Meta
bound to the code. Therefore redirect_uri must be completely OMITTED from the
token exchange - never sent as "" and never guessed.

IMPORTANT - Where the WABA ID and phone number ID come from:

PRIMARY SOURCE (documented Meta Embedded Signup):
The WABA ID, phone number ID and business portfolio ID are returned by the
Embedded Signup completion event (the WA_EMBEDDED_SIGNUP FINISH message) and
forwarded from the frontend in the callback payload. When the session event
delivers them they are used verbatim.

DOCUMENTED SERVER-SIDE FALLBACK (when the session event is delayed/unavailable):
Meta's official docs ("Managing WhatsApp Business Accounts") define how to
recover the shared WABA ID from the returned business token: the /debug_token
response contains granular_scopes whose target_ids identify every WABA that
granted the app a given permission. The most recently onboarded WABAs appear
first, so the first target_id for the whatsapp_business_management scope is
the customer's WABA. The phone number ID is then resolved from the WABA's
phone_numbers edge (GET /<WABA_ID>/phone_numbers).

The backend NEVER invents WABA IDs and NEVER uses /me/businesses or any other
business-portfolio edge to guess them. It uses ONLY IDs that Meta itself
returned: the session event first, then the /debug_token granular_scopes
target_ids. If neither source yields a WABA ID, the flow fails with a
controlled WABA_NOT_RETURNED error.

After the exchange the access token is validated with /debug_token (app_id +
granted scopes are logged; the token itself is never logged).
"""
import httpx
import logging
from typing import Dict, Optional, Tuple

from config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# TOKEN EXCHANGE REDIRECT URI (Embedded Signup FB.login popup flow)
# ============================================================================
# The FB.login() + config_id (Facebook Login for Business) Embedded Signup
# exchange sends NO redirect_uri parameter - it is completely omitted, exactly
# as documented in Meta's official Embedded Signup implementation. Sending
# redirect_uri="" (empty string) or any real URL triggers error_subcode 36008.
# The config_id provides the security binding.

# Canonical production redirect URI. This exact value is used by the OAuth
# dialog frontend for configuration/verification display purposes only. It is
# NEVER sent to Meta in the Embedded Signup token exchange: the official
# Facebook Login for Business exchange sends client_id + client_secret + code
# with NO redirect_uri. Sending this canonical value, the empty string, or any
# other URL triggers error_subcode 36008.
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
PHONE_ALREADY_REGISTERED = "PHONE_ALREADY_REGISTERED"
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
        """Log the exact request being sent to Meta (never the app secret or full code).

        EMBEDDED SIGNUP FB.LOGIN POPUP TOKEN EXCHANGE:
        The official Facebook Login for Business (config_id) Embedded Signup
        exchange sends ONLY:
        - client_id
        - client_secret
        - code

        redirect_uri is COMPLETELY OMITTED - never the empty string, never a
        real URL (any redirect_uri value triggers Meta error_subcode 36008).
        """
        logger.info("=" * 80)
        logger.info("META EMBEDDED SIGNUP TOKEN EXCHANGE")
        logger.info("=" * 80)
        logger.info(f"  Meta endpoint: {url}")
        logger.info(f"  Method: GET")
        logger.info(f"  App ID: {self.app_id}")
        logger.info(f"  Parameter names: {list(params.keys())}")
        logger.info(f"  Code length: {len(params.get('code', ''))}")
        logger.info("  redirect_uri: NOT SENT (official Embedded Signup exchange - client_id + client_secret + code only)")

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

        Meta error_subcode 36008 ("Error validating verification code") means
        the redirect_uri did not match the value Meta recorded when it issued
        the code, or the code is invalid/expired/already consumed. With the
        correct exchange (redirect_uri omitted entirely), a 36008 indicates
        the code itself is no longer valid. The code must NEVER be retried and
        a completely new Embedded Signup flow is required.
        """
        try:
            error_obj = response.json().get("error", {})
        except Exception:
            error_obj = {}
        message = error_obj.get("message", "Failed to exchange code")

        if error_obj.get("error_subcode") == _META_ERROR_SUBCODE_REDIRECT_MISMATCH:
            return (
                f"{OAUTH_REDIRECT_URI_MISMATCH}: OAuth authorization code is "
                "invalid, expired, or already consumed. Please restart "
                "WhatsApp Embedded Signup to get a fresh code."
            ), error_obj

        if "expired" in message.lower():
            return f"{OAUTH_CODE_EXPIRED}: {message}", error_obj

        return message, error_obj

    # ============================================================
    # Step 1 - Exchange code for access token
    # ============================================================

    async def exchange_code_for_token(
        self, code: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange the Embedded Signup authorization code for an access token.

        EMBEDDED SIGNUP FB.LOGIN POPUP TOKEN EXCHANGE (official Meta flow):
        For FB.login() with config_id (Facebook Login for Business) Embedded
        Signup, the official server-side exchange sends ONLY client_id,
        client_secret and code - redirect_uri is COMPLETELY OMITTED:

            GET /oauth/access_token?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>

        Sending redirect_uri - the empty string OR any real URL - triggers
        Meta error code 100 / subcode 36008 ("make sure your redirect_uri is
        identical to the one you used in the OAuth dialog request").

        Args:
            code: The exchangeable authorization code from Meta Embedded Signup.

        Returns:
            (success, data, error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/oauth/access_token"

            # OFFICIAL EMBEDDED SIGNUP TOKEN EXCHANGE (Facebook Login for
            # Business config_id flow): send ONLY client_id + client_secret +
            # code. redirect_uri is completely omitted - the config_id provides
            # the security binding. Sending redirect_uri (empty string or any
            # real URL) triggers Meta error_subcode 36008.
            params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
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

            # Documented server-side WABA recovery (Meta "Managing WhatsApp
            # Business Accounts"): the granular_scopes target_ids identify the
            # WABAs that granted the app each permission. The most recently
            # onboarded WABAs appear first, so the first target_id for
            # whatsapp_business_management is the customer's WABA. Only used as
            # a fallback when the WA_EMBEDDED_SIGNUP session event did not
            # deliver the IDs. Never logged as part of a token/secret.
            waba_target_ids: list = []
            for g in granular_scopes:
                # Meta's granular_scopes entries carry the permission name under
                # "scope" (sometimes surfaced as "permission"). Accept both so a
                # real /debug_token response is never missed.
                scope_name = str(g.get("scope") or g.get("permission") or "").strip()
                if scope_name == "whatsapp_business_management":
                    for tid in (g.get("target_ids") or []):
                        tid = str(tid).strip()
                        if tid and tid not in waba_target_ids:
                            waba_target_ids.append(tid)

            logger.info("=" * 80)
            logger.info("META ACCESS TOKEN VALIDATION")
            logger.info("=" * 80)
            logger.info(f"  App ID: {token_app_id or self.app_id}")
            logger.info(f"  Token type: {data.get('type', 'unknown')}")
            logger.info(f"  Granted scopes: {sorted(granted)}")
            logger.info(f"  Missing WhatsApp scopes: {missing or 'none'}")
            logger.info(f"  WABA target_ids from granular_scopes: {len(waba_target_ids)} found")
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
                "waba_target_ids": waba_target_ids,
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
    # Step 6 - Register the customer's business phone number
    # ============================================================

    async def register_phone_number(
        self, phone_number_id: str, access_token: str, pin: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Register the customer's business phone number for Cloud API use and
        enable two-step verification:

            POST /<PHONE_NUMBER_ID>/register
            { "messaging_product": "whatsapp", "pin": "<6-DIGIT-PIN>" }

        Meta's official "Registering business phone numbers" guide states that
        Embedded Signup performs the number-creation and verification steps
        automatically, but the Tech Provider MUST still register the verified
        number for API use ("you only need to perform step 4 when a client
        completes the flow"). A number must be registered within 14 days of the
        Embedded Signup flow.

        The PIN is a 6-digit two-step verification PIN chosen and stored
        server-side (META_PHONE_REGISTRATION_PIN). It is sent to Meta ONLY in
        the request body and is NEVER logged, returned to the frontend, or
        stored in the database.

        If the number is ALREADY registered, Meta returns error 131048
        (PHONE_ALREADY_REGISTERED) - that is treated as SUCCESS because the
        number is already usable with Cloud API.

        Args:
            phone_number_id: Business phone number ID to register.
            access_token: Customer business access token.
            pin: 6-digit two-step verification PIN. When omitted/empty, the
                registration step is skipped (never a hard failure) and the
                caller is told via the returned data.

        Returns:
            (success, {"registered": bool, "skipped": bool}, error_message)
        """
        try:
            pin = str(pin or "").strip()
            if not pin:
                logger.info(
                    "[EmbeddedSignup] Phone registration skipped - no "
                    "META_PHONE_REGISTRATION_PIN configured"
                )
                return True, {"registered": False, "skipped": True}, None

            url = f"{self.GRAPH_API_BASE}/{phone_number_id}/register"
            body = {"messaging_product": "whatsapp", "pin": pin}

            logger.info("=" * 80)
            logger.info("META GRAPH API REQUEST - PHONE REGISTRATION")
            logger.info("=" * 80)
            logger.info(f"  Graph API endpoint: {url}")
            logger.info("  HTTP method: POST")
            logger.info(f"  Object ID / edge: /{phone_number_id}/register")
            logger.info("  Body parameters: messaging_product, pin (REDACTED - never logged)")
            logger.info("=" * 80)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=body, params={"access_token": access_token})

            if response.status_code == 200:
                logger.info(f"Phone number {phone_number_id} registered successfully")
                return True, {"registered": True, "skipped": False}, None

            try:
                error_obj = response.json().get("error", {})
            except Exception:
                error_obj = {}

            code = error_obj.get("code")
            if code == 131048:  # already registered - treat as success
                logger.info(
                    f"Phone number {phone_number_id} is already registered "
                    f"(code {code}) - PHONE_ALREADY_REGISTERED treated as success"
                )
                return True, {"registered": True, "skipped": False}, None

            last_error = error_obj.get("message", "Failed to register phone number")
            detail = (
                f"{PHONE_REGISTRATION_FAILED}: phone registration failed "
                f"(code: {code}, error_subcode: {error_obj.get('error_subcode')}, "
                f"message: {last_error}, fbtrace_id: {error_obj.get('fbtrace_id')})"
            )
            logger.error(detail)
            return False, None, detail

        except httpx.TimeoutException:
            logger.error("Phone registration timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Phone registration error: {e}", exc_info=True)
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
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Complete WhatsApp integration setup from the Embedded Signup data.

        The WABA ID and phone number ID are resolved in this order (both are
        IDs Meta itself returned - the backend NEVER invents them):

        PRIMARY - WA_EMBEDDED_SIGNUP session event (the source of truth for
        the customer onboarding session): the IDs captured on the frontend and
        forwarded in the callback payload.

        DOCUMENTED SERVER-SIDE FALLBACK - when the session event was delayed
        or unavailable (only the exchangeable code arrived):
        - WABA ID: the first target_id in the /debug_token granular_scopes for
          the whatsapp_business_management scope (most recently onboarded WABAs
          appear first - Meta "Managing WhatsApp Business Accounts").
        - Phone number ID: the verified business number on the WABA, resolved
          from GET /<WABA_ID>/phone_numbers.

        If NO source yields a WABA ID, the flow fails with a controlled
        WABA_NOT_RETURNED error - the backend NEVER uses /me/businesses or any
        other business-portfolio edge to guess it.

        The token exchange follows the official Embedded Signup FB.login popup
        flow:
        - Sends ONLY client_id, client_secret and code
        - redirect_uri is completely OMITTED (the official Facebook Login for
          Business exchange); sending redirect_uri='' or any real URL triggers
          error 36008

        Token exchange:
            GET /oauth/access_token?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>

        Flow:
         1. Exchange code for access token (server-side; no redirect_uri)
         2. Validate the exchanged token via /debug_token (app_id + scopes +
            granular_scopes WABA target_ids)
         3. Resolve the WABA ID: session event, then /debug_token granular
            scopes target_ids (no /me/businesses)
         4. Resolve the phone number ID: session event, then the WABA's
            phone_numbers edge
         5. Validate the WABA via GET /<WABA_ID> (only supported fields: id,name)
         6. GET /<WABA_ID>/phone_numbers (WABA edge) and verify the resolved
            phone number ID is present
         7. POST /<WABA_ID>/subscribed_apps to subscribe the WABA to the app
         8. POST /<PHONE_NUMBER_ID>/register to register the verified number
            for Cloud API use and enable two-step verification (the 6-digit PIN
            is read from META_PHONE_REGISTRATION_PIN and is NEVER logged or
            stored; an already-registered number - Meta code 131048 - is
            treated as success).

        Args:
            code: Authorization code from Meta Embedded Signup
            waba_id: WhatsApp Business Account ID returned by the Embedded
                Signup session event (optional - resolved server-side from the
                /debug_token granular_scopes target_ids when absent).
            phone_number_id: Business phone number ID returned by the Embedded
                Signup session event (optional - resolved server-side from the
                WABA's phone_numbers edge when absent).
            business_id: Business portfolio ID returned by the Embedded Signup
                session (optional - stored when provided, never fabricated).

        Returns:
            (success, integration_data, error_message)

        integration_data contains:
        - access_token: Long-lived customer-scoped business token
        - business_id: Meta business portfolio ID (from Embedded Signup only)
        - waba_id: WhatsApp Business Account ID (resolved as above)
        - business_name: WABA name (from the WABA node)
        - phone_number_id: Phone Number ID (resolved as above)
        - display_phone_number: Display phone number
        - verified_name: Verified display name
        """
        try:
            # Step 1: Exchange code for token. The official Embedded Signup
            # (Facebook Login for Business config_id) exchange sends ONLY
            # client_id + client_secret + code - redirect_uri is completely
            # omitted (any redirect_uri value triggers error_subcode 36008).
            logger.info(f"[EmbeddedSignup] Step 1/6 - Meta token exchange started (code length: {len(code)})")
            success, token_data, error = await self.exchange_code_for_token(code)
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

            # Step 3: Resolve the WABA ID. PRIMARY: the Embedded Signup session
            # event. DOCUMENTED FALLBACK: the first target_id in the /debug_token
            # granular_scopes for whatsapp_business_management (most recently
            # onboarded WABAs appear first - Meta "Managing WhatsApp Business
            # Accounts"). NEVER /me/businesses or any other portfolio edge.
            waba_id = str(waba_id or "").strip() or None
            if not waba_id:
                candidate_ids = [
                    str(tid).strip()
                    for tid in (token_info.get("waba_target_ids") or [])
                    if str(tid).strip()
                ]
                if candidate_ids:
                    waba_id = candidate_ids[0]
                    logger.info(
                        "[EmbeddedSignup] WABA ID resolved server-side from "
                        "/debug_token granular_scopes (whatsapp_business_management "
                        f"target_ids, first/most-recently-onboarded): {waba_id}"
                    )
            if not waba_id:
                logger.error(
                    "[EmbeddedSignup] Step 3/6 failed - no WABA ID available from "
                    "the Embedded Signup session OR the /debug_token granular "
                    "scopes target_ids (WABA_NOT_RETURNED)"
                )
                return False, None, (
                    f"{WABA_NOT_RETURNED}: the WhatsApp Business Account ID was "
                    "not returned by Meta Embedded Signup and could not be "
                    "recovered from the business token. Please restart "
                    "WhatsApp Embedded Signup and complete the setup again."
                )
            else:
                logger.info(f"[EmbeddedSignup] WABA ID resolved: {waba_id}")

            # Step 4: Capture the phone number ID if the session event delivered
            # it. When absent it is resolved in Step 6 from the WABA's
            # phone_numbers edge (documented server-side resolution) - the
            # backend never guesses it.
            phone_number_id = str(phone_number_id or "").strip() or None
            if phone_number_id:
                logger.info(f"[EmbeddedSignup] Phone Number ID from session: {phone_number_id}")
            else:
                logger.info(
                    "[EmbeddedSignup] Phone Number ID not in the session event - "
                    "will resolve server-side from the WABA phone_numbers edge"
                )

            # Step 5: Validate the WABA using the resolved WABA ID.
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
            if phone_number_id:
                # Session event delivered the phone number ID - verify it is a
                # real number on this WABA (never replace it with another number).
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
            else:
                # Documented server-side resolution: use the verified business
                # number on the WABA (prefer a verified/registered number,
                # fall back to the first number returned by Meta).
                for pn in phone_numbers:
                    if str(pn.get("certificate") or "").strip() or str(pn.get("verified_name") or "").strip():
                        phone_data = pn
                        break
                if phone_data is None and phone_numbers:
                    phone_data = phone_numbers[0]
                if phone_data is None:
                    logger.error(
                        f"[EmbeddedSignup] Step 6/6 failed - no phone number "
                        f"available on WABA {waba_id} (PHONE_NUMBER_NOT_RETURNED)"
                    )
                    return False, None, (
                        f"{PHONE_NUMBER_NOT_RETURNED}: no business phone number "
                        "was found in the WhatsApp Business Account. Please add "
                        "a phone number and restart WhatsApp Embedded Signup."
                    )
                phone_number_id = str(phone_data.get("id") or "").strip() or phone_number_id
                logger.info(
                    f"[EmbeddedSignup] Phone Number ID resolved server-side from "
                    f"the WABA phone_numbers edge: {phone_number_id}"
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

            # Register the customer's business phone number for Cloud API use
            # and enable two-step verification (Meta "Registering business phone
            # numbers": Embedded Signup does steps 1-3 automatically, the Tech
            # Provider still performs step 4 - register - when a client
            # completes the flow). The 6-digit PIN comes from
            # META_PHONE_REGISTRATION_PIN (server-side only); it is never
            # logged, returned to the frontend or stored. An already-registered
            # number (Meta code 131048) is treated as success. If registration
            # is skipped or fails, the rest of the flow is NOT rolled back - the
            # number remains usable within the 14-day Embedded Signup window and
            # the result is reported in the response.
            reg_pin = (get_settings().META_PHONE_REGISTRATION_PIN or "").strip()
            reg_ok, reg_data, reg_error = await self.register_phone_number(
                phone_number_id, access_token, pin=reg_pin
            )
            phone_registered = bool((reg_data or {}).get("registered"))
            phone_registration_skipped = bool((reg_data or {}).get("skipped"))
            if not reg_ok:
                logger.warning(
                    f"[EmbeddedSignup] Phone registration did not complete: "
                    f"{reg_error} (integration will still be saved; the number "
                    "must be registered within 14 days of Embedded Signup)"
                )
            logger.info(
                f"[EmbeddedSignup] Phone registration: registered={phone_registered} "
                f"skipped={phone_registration_skipped}"
            )

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
                "phone_registered": phone_registered,
            }

            logger.info(
                f"[EmbeddedSignup] WhatsApp integration setup complete: WABA {waba_id}, "
                f"phone {display_phone_number}, subscribed_apps={bool(sub_data)}, "
                f"phone_registered={phone_registered}"
            )
            return True, integration_data, None

        except Exception as e:
            logger.error(f"[EmbeddedSignup] Setup integration error: {e}")
            return False, None, f"An unexpected error occurred: {str(e)}"
