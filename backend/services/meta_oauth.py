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
forwarded from the frontend in the callback payload. The backend uses those
supplied IDs directly: GET /<WABA_ID> to validate the WABA, GET
/<WABA_ID>/phone_numbers to retrieve the phone number, and POST
/<WABA_ID>/subscribed_apps to subscribe the app.

When the asset IDs are NOT present in the payload (an edge case - e.g. the
popup's session message did not arrive), the backend falls back to resolving
them from the token via the business portfolio edges:

    1. GET /me/businesses?fields=id,name
       -> the business portfolio(s) the token can access
    2. GET /<business_id>/client_whatsapp_business_accounts?fields=id,name
       -> WABAs shared with the portfolio by Embedded Signup
       (fallback edge: /<business_id>/owned_whatsapp_business_accounts)
    3. GET /<WABA_ID>/phone_numbers?access_token=<BUSINESS_TOKEN>
       -> the business phone number

The debug_token endpoint is NOT used for WABA discovery. Its granular_scopes
entries list permission scopes, and for a Business Integration System User
token inspected with the app access token (access_token=<APP_ID>|<APP_SECRET>)
the whatsapp_business_management / whatsapp_business_messaging scopes come back
WITHOUT the WABA target_ids populated (Meta's docs call /debug_token for this
purpose with a System User token in the Authorization header).
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

        When Meta reports error_subcode 36008 (verification-code validation
        failure) an actionable hint is appended. The hint explains that the
        exchange redirect_uri must be byte-identical to the canonical production
        value (https://apps.orvym.com/dashboard/integrations/) and registered in
        Valid OAuth Redirect URIs. It never suggests guessing or dropping
        redirect_uri.
        """
        try:
            error_obj = response.json().get("error", {})
        except Exception:
            error_obj = {}
        message = error_obj.get("message", "Failed to exchange code")
        if error_obj.get("error_subcode") == 36008:
            message = (
                f"{message} (hint: error_subcode 36008 means the exchange "
                "redirect_uri does not match the value Meta recorded for this "
                "single-use code. Confirm the exchange sent the canonical "
                "redirect_uri exactly as "
                "https://apps.orvym.com/dashboard/integrations/ (never omitted, "
                "never an empty string), that the same exact value is used in "
                "the OAuth dialog request and registered in the Meta App "
                "Dashboard Valid OAuth Redirect URIs, and that the code was "
                "exchanged exactly once within its short TTL.)"
            )
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
    # Step 2 - Identify the WABA ID(s) granted to the access token
    # ============================================================

    async def get_businesses_from_token(self, access_token: str) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Resolve the business portfolio(s) associated with the access token via
        the documented Business edge:

            GET /me/businesses?fields=id,name&access_token=<TOKEN>

        This returns the business portfolios the Embedded Signup token can
        access. The business portfolio ID is what the WABA edges
        (client_whatsapp_business_accounts / owned_whatsapp_business_accounts)
        are read from.

        Args:
            access_token: The business access token returned by the exchange.

        Returns:
            (success, [{"id": str, "name": str}, ...], error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/me/businesses"
            params = {
                "fields": "id,name",
                "access_token": access_token,
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, error_obj = self._parse_error(response)
                logger.error(
                    f"Resolve business portfolios failed: {last_error} "
                    f"(code: {error_obj.get('code')}, subcode: {error_obj.get('error_subcode')})"
                )
                return False, None, last_error or "Failed to resolve the business portfolios for this token"

            businesses = response.json().get("data") or []
            logger.info(
                f"Business portfolios resolved from token: "
                f"{[(b.get('id'), b.get('name')) for b in businesses]}"
            )
            return True, businesses, None

        except httpx.TimeoutException:
            logger.error("Resolve business portfolios timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Resolve business portfolios error: {e}", exc_info=True)
            return False, None, str(e)

    async def get_business_wabas(self, business_id: str, edge: str, access_token: str) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Read the WhatsApp Business Accounts of a business portfolio from the
        documented WhatsApp Business Account edges of the Business node:

            GET /<business_id>/<edge>?fields=id,name&access_token=<TOKEN>

        edge is one of:
          - client_whatsapp_business_accounts: WABAs shared with the business
            portfolio by Embedded Signup ("Get list of shared WABAs")
          - owned_whatsapp_business_accounts:   WABAs owned by the portfolio

        Args:
            business_id: The business portfolio ID (from /me/businesses or the
                Embedded Signup completion message).
            edge: "client_whatsapp_business_accounts" or
                  "owned_whatsapp_business_accounts".
            access_token: The business access token returned by the exchange.

        Returns:
            (success, [{"id": str, "name": str}, ...], error_message)
        """
        try:
            url = f"{self.GRAPH_API_BASE}/{business_id}/{edge}"
            params = {
                "fields": "id,name",
                "access_token": access_token,
            }

            self._log_graph_request("GET", url, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                last_error, error_obj = self._parse_error(response)
                logger.info(
                    f"GET /{business_id}/{edge} unavailable: {last_error} "
                    f"(code: {error_obj.get('code')}, subcode: {error_obj.get('error_subcode')})"
                )
                return False, None, last_error or "Failed to read the WhatsApp Business Account list"

            wabas = response.json().get("data") or []
            logger.info(f"WABAs via /{business_id}/{edge}: {[w.get('id') for w in wabas]}")
            return True, wabas, None

        except httpx.TimeoutException:
            logger.error(f"GET /{business_id}/{edge} timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"GET /{business_id}/{edge} error: {e}", exc_info=True)
            return False, None, str(e)

    async def discover_shared_waba_from_token(self, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Identify the WhatsApp Business Account (WABA) ID(s) and the business
        portfolio granted to an Embedded Signup access token.

        Uses Meta's documented business portfolio edges (NOT debug_token
        granular_scopes - the granular scopes of a Business Integration System
        User token inspected with the app access token do not include the WABA
        target_ids):

            1. GET /me/businesses?fields=id,name
               -> the business portfolio(s) the token can access
            2. GET /<business_id>/client_whatsapp_business_accounts?fields=id,name
               -> WABAs shared with the portfolio by Embedded Signup
            3. Fallback: GET /<business_id>/owned_whatsapp_business_accounts
               -> WABAs owned directly by the portfolio

        The business portfolios are iterated in order; the first portfolio that
        exposes any WABA wins. The discovered business portfolio ID is the
        genuine tenant business ID (never fabricated).

        Args:
            access_token: The business access token returned by the exchange.

        Returns:
            (success, {"waba_ids": [str, ...], "business_id": str|None,
                       "business_name": str|None}, error_message)
        """
        try:
            # 1. Resolve the business portfolio(s) the token can access
            ok, businesses, error = await self.get_businesses_from_token(access_token)
            if not ok:
                return False, None, error or "Failed to discover the WhatsApp Business Account"
            if not businesses:
                logger.error("/me/businesses returned no business portfolios for this token")
                return False, None, (
                    "No WhatsApp Business Account found. The access token is not "
                    "associated with a business portfolio. Complete WhatsApp "
                    "Business setup and try again."
                )

            waba_ids: list = []
            business_id = None
            business_name = None
            for biz in businesses:
                biz_id = str(biz.get("id") or "").strip()
                if not biz_id:
                    continue
                if business_id is None:
                    business_id = biz_id
                    business_name = biz.get("name") or ""

                # 2. Shared WABAs first, then owned WABAs as a fallback edge
                for edge in ("client_whatsapp_business_accounts", "owned_whatsapp_business_accounts"):
                    ok_edge, wabas, edge_error = await self.get_business_wabas(biz_id, edge, access_token)
                    if not ok_edge:
                        logger.info(
                            f"Edge /{biz_id}/{edge} unavailable ({edge_error}) - trying next source"
                        )
                        continue
                    for waba in wabas:
                        wid = str(waba.get("id") or "").strip()
                        if wid and wid not in waba_ids:
                            waba_ids.append(wid)
                    if waba_ids:
                        break

                if waba_ids:
                    break

            logger.info(f"WABA discovery via business edges - WABA IDs identified: {waba_ids}")

            if not waba_ids:
                logger.error(
                    "No WABA IDs found via /me/businesses + "
                    "client/owned_whatsapp_business_accounts edges"
                )
                return False, None, (
                    "No WhatsApp Business Account found. Complete WhatsApp "
                    "Business setup and try again."
                )

            return True, {
                "waba_ids": waba_ids,
                "business_id": business_id,
                "business_name": business_name,
            }, None

        except httpx.TimeoutException:
            logger.error("WABA discovery timed out")
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"WABA discovery error: {e}", exc_info=True)
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

        The WABA ID and phone number ID MAY be returned by Meta Embedded Signup
        in the WA_EMBEDDED_SIGNUP session message (captured on the frontend and
        forwarded here). The backend uses those supplied IDs directly. Only
        when they are NOT provided does the backend discover them server-side
        from the token using Meta's documented business portfolio edges (NOT
        debug_token granular_scopes):
        GET /me/businesses -> the business portfolio, then
        GET /<business_id>/client_whatsapp_business_accounts -> the WABA IDs
        shared with the portfolio by Embedded Signup. The code is never used to
        guess the WABA - only to obtain the token, which is then inspected.

        The code exchange ALWAYS sends the canonical production redirect_uri
        (https://apps.orvym.com/dashboard/integrations/) - it is NEVER omitted
        and NEVER sent empty. A mismatched or missing redirect_uri fails the
        exchange with error_subcode 36008.

        Flow:
        1. Exchange code for access token (server-side, always with the
           canonical redirect_uri)
        2. If no WABA ID was provided, discover it via the business portfolio
           edges (GET /me/businesses -> /client_whatsapp_business_accounts)
        3. Validate the WABA via GET /<WABA_ID> (only supported fields: id,name)
        4. GET /<WABA_ID>/phone_numbers (WABA edge) to retrieve the phone number
        5. Verify the returned phone number ID matches Embedded Signup's (when
           provided, otherwise use the first phone number on the WABA)
        6. POST /<WABA_ID>/subscribed_apps to subscribe the WABA to the app

        Args:
            code: Authorization code from Meta Embedded Signup
            waba_id: WhatsApp Business Account ID returned by Embedded Signup
                (optional - discovered server-side when omitted).
            phone_number_id: Business phone number ID returned by Embedded Signup
                (optional - first phone number used when omitted).
            business_id: Business portfolio ID returned by Embedded Signup
                (optional - falls back to the portfolio resolved from the token
                when omitted).
            redirect_uri: The EXACT redirect_uri used in the OAuth dialog
                request. Optional - when omitted or empty the canonical
                production redirect_uri is used. redirect_uri is NEVER omitted
                from the exchange and NEVER sent empty.

        Returns:
            (success, integration_data, error_message)

        integration_data contains:
        - access_token: Long-lived customer-scoped business token
        - business_id: Meta business portfolio ID (from Embedded Signup or
          resolved via /me/businesses)
        - waba_id: WhatsApp Business Account ID (from Embedded Signup or
          discovered via the business portfolio edges)
        - business_name: WABA name (from the WABA node)
        - phone_number_id: Phone Number ID
        - display_phone_number: Display phone number
        - verified_name: Verified display name
        """
        try:
            # Step 1: Exchange code for token. The exchange ALWAYS sends the
            # canonical production redirect_uri (see module docstring and
            # exchange_code_for_token) - it is never omitted and never empty.
            logger.info(f"[EmbeddedSignup] Step 1/5 - Meta token exchange started (code length: {len(code)})")
            success, token_data, error = await self.exchange_code_for_token(code, redirect_uri=redirect_uri)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 1/5 failed - Token exchange: {error}")
                return False, None, error or "Failed to exchange authorization code"
            logger.info("[EmbeddedSignup] Step 1/5 - Meta token exchange succeeded")
            access_token = token_data.get("access_token")

            # Step 2: Resolve the WABA ID. When Embedded Signup did not return
            # one (current production flow delivers only the exchangeable code),
            # discover it server-side from the token using Meta's documented
            # business portfolio edges: GET /me/businesses -> the portfolio,
            # then GET /<business_id>/client_whatsapp_business_accounts -> the
            # WABAs shared with the portfolio by Embedded Signup.
            if not waba_id:
                logger.info("[EmbeddedSignup] Step 2/5 - No WABA ID supplied, discovering via business portfolio edges")
                success, token_info, error = await self.discover_shared_waba_from_token(access_token)
                if not success:
                    logger.error(f"[EmbeddedSignup] Step 2/5 failed - WABA discovery: {error}")
                    return False, None, error or "Failed to discover the WhatsApp Business Account"
                discovered_waba_ids = token_info.get("waba_ids") or []
                if not discovered_waba_ids:
                    logger.error("[EmbeddedSignup] Step 2/5 failed - business edges returned no WABA IDs")
                    return False, None, "No WhatsApp Business Account found. Complete WhatsApp Business setup and try again."
                waba_id = str(discovered_waba_ids[0])
                # The portfolio resolved from /me/businesses is the genuine Meta
                # business the token belongs to. Use it as the tenant business
                # ID only when Embedded Signup did not supply one (never
                # fabricate a value).
                if not business_id:
                    business_id = token_info.get("business_id")
                logger.info(f"[EmbeddedSignup] Step 2/5 - WABA discovered via business edges: {waba_id}")

            logger.info(f"[EmbeddedSignup] Step 2/5 - WABA validation started (waba_id: {waba_id})")
            success, waba_data, error = await self.get_waba_details(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 2/5 failed - WABA validation for {waba_id}: {error}")
                return False, None, error or "Failed to validate the WhatsApp Business Account"
            business_name = waba_data.get("name", "")
            logger.info(f"[EmbeddedSignup] Step 2/5 - WABA validation succeeded (name: {business_name})")

            # Step 3: Get phone numbers from the WABA's phone_numbers EDGE
            logger.info(f"[EmbeddedSignup] Step 3/5 - Phone numbers lookup started (waba_id: {waba_id})")
            success, phone_numbers, error = await self.get_phone_numbers(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 3/5 failed - Phone numbers for WABA {waba_id}: {error}")
                return False, None, error or "Failed to retrieve phone numbers"
            logger.info("[EmbeddedSignup] Step 3/5 - Phone numbers lookup succeeded")

            # Step 4: Verify the phone number matches the one Embedded Signup returned
            phone_data = None
            if phone_number_id:
                for pn in phone_numbers:
                    if str(pn.get("id")) == str(phone_number_id):
                        phone_data = pn
                        break
                if phone_data is None:
                    logger.error(
                        f"[EmbeddedSignup] Step 4/5 failed - Phone number {phone_number_id} "
                        f"not found in WABA {waba_id}"
                    )
                    return False, None, (
                        "Phone number validation failed: the phone number ID returned "
                        "by Embedded Signup was not found in the WhatsApp Business "
                        "Account. Please reconnect WhatsApp."
                    )
            elif phone_numbers:
                phone_data = phone_numbers[0]
            else:
                logger.error(
                    f"[EmbeddedSignup] Step 4/5 failed - WABA {waba_id} has no phone numbers"
                )
                return False, None, (
                    "No phone number found: the WhatsApp Business Account has no "
                    "business phone number. Please add one and reconnect WhatsApp."
                )

            phone_number_id_final = phone_data.get("id")
            display_phone_number = phone_data.get("display_phone_number", "")
            verified_name = phone_data.get("verified_name", "")
            logger.info(
                f"[EmbeddedSignup] Step 4/5 - Phone number verified: {display_phone_number} "
                f"(id: {phone_number_id_final}, verified_name: {verified_name})"
            )

            # Step 5: Subscribe the WABA to the app (required for webhooks)
            logger.info(f"[EmbeddedSignup] Step 5/5 - WABA subscription started (waba_id: {waba_id})")
            success, sub_data, error = await self.subscribe_to_waba(waba_id, access_token)
            if not success:
                logger.error(f"[EmbeddedSignup] Step 5/5 failed - WABA subscription for {waba_id}: {error}")
                return False, None, error or "Failed to subscribe the WhatsApp Business Account to the app"
            logger.info("[EmbeddedSignup] Step 5/5 - WABA subscription succeeded")

            # Business ID validation (non-fatal): use only the actual ID returned
            # by Embedded Signup. Never invent or guess one.
            if business_id:
                business_id = str(business_id).strip()
                if not business_id:
                    business_id = None
            logger.info(f"[EmbeddedSignup] Business ID for tenant record: {business_id or 'not provided'}")

            integration_data = {
                "access_token": access_token,
                "business_id": business_id or "",
                "waba_id": waba_id,
                "business_name": business_name,
                "phone_number_id": phone_number_id_final,
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
