"""
Comprehensive mock-based tests for MetaOAuthService.exchange_code_for_token.

These tests verify the EXACT HTTP request the backend sends to Meta:
  - endpoint URL
  - query parameters
  - redirect_uri handling (empty string "" for the Embedded Signup FB.login
    popup flow; a custom non-canonical value forwarded verbatim)
  - success and error handling

They mock httpx.AsyncClient so no real network call is made.
"""
import asyncio
import json
from unittest import mock

from services.meta_oauth import MetaOAuthService

GRAPH_BASE = "https://graph.facebook.com/v26.0"


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


def captured_request(captured, status_code, payload):
    """Return an AsyncClient mock that records the request it received."""
    client = mock.AsyncMock()
    response = FakeResponse(status_code, payload)
    # Make `async with client as c` yield the SAME mock that records requests
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    async def fake_get(url, params=None):
        captured["url"] = url
        captured["params"] = dict(params or {})
        return response

    client.get.side_effect = fake_get
    return client


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_exchange_sends_empty_redirect_uri_by_default():
    """
    The exchange ALWAYS includes redirect_uri. When invoked WITHOUT an explicit
    redirect_uri (or with the canonical value) the Embedded Signup FB.login
    popup flow sends redirect_uri="" - the code is bound to Meta's internal
    redirect URI, and sending the canonical value is exactly what triggers
    Meta error_subcode 36008.
    """
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("x" * 449)

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer", "expires_in": 5184000}
    )):
        ok, data, err = run(svc.exchange_code_for_token(code))

    assert ok is True, err
    assert data["access_token"] == "EAA_token"
    assert captured["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["client_secret"] == "secret"
    assert captured["params"]["code"] == code
    assert captured["params"]["redirect_uri"] == "", \
        "Embedded Signup exchange must send redirect_uri='' (never the canonical value)"
    print("PASS: exchange always sends redirect_uri='' for the Embedded Signup flow")

    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "redirect_uri"}


def test_exchange_without_redirect_uri_sends_empty():
    """When no redirect_uri is supplied the exchange sends redirect_uri=''."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode"))

    assert ok is True, err
    assert captured["params"]["redirect_uri"] == ""
    print("PASS: redirect_uri sent as '' when no value is supplied")


def test_exchange_does_not_forward_canonical_redirect_uri():
    """
    The canonical value (https://apps.orvym.com/dashboard/integrations/) is what
    production's frontend payload sends, but it is NOT what Meta recorded for
    the FB.login popup code - it is replaced with "" in the exchange to avoid
    error_subcode 36008.
    """
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("r" * 449)
    redirect_uri = "https://apps.orvym.com/dashboard/integrations/"

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token(code, redirect_uri=redirect_uri))

    assert ok is True, err
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code
    assert captured["params"]["redirect_uri"] == "", \
        "the canonical redirect_uri must NOT be forwarded to Meta (it causes 36008)"
    print("PASS: canonical redirect_uri replaced with '' in the exchange")


def test_exchange_forwards_custom_redirect_uri_verbatim():
    """
    A genuinely custom, non-canonical redirect_uri (manual OAuth dialog flow)
    is forwarded verbatim (byte-for-byte) to Meta's "redirect_uri identical"
    check.
    """
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("s" * 449)
    redirect_uri = "https://manual-dialog.example.com/callback"

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token(code, redirect_uri=redirect_uri))

    assert ok is True, err
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code
    assert captured["params"]["redirect_uri"] == redirect_uri, \
        "custom redirect_uri must be forwarded byte-identically"
    print("PASS: custom redirect_uri forwarded verbatim to Meta")


def test_exchange_empty_string_redirect_uri_stays_empty():
    """redirect_uri='' (whitespace) must stay empty - the canonical value must not be substituted."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode", redirect_uri="   "))

    assert ok is True, err
    assert captured["params"]["redirect_uri"] == "", \
        "empty/whitespace redirect_uri must stay empty in the exchange"
    print("PASS: empty-string redirect_uri is sent as '' - canonical value not substituted")


def test_exchange_meta_error_returned():
    """Meta 400 errors (e.g. redirect_uri validation) must propagate to caller."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    error_payload = {
        "error": {
            "message": "Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request",
            "type": "OAuthException", "code": 100, "error_subcode": 36008,
            "fbtrace_id": "AAH5Klp99JmQfQsk2MSLckg",
        }
    }

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 400, error_payload
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode"))

    assert ok is False
    assert data is None
    assert "OAUTH_REDIRECT_URI_MISMATCH" in err, err
    assert "redirect_uri" in err.lower() or "redirect URI" in err, err
    assert captured["params"]["redirect_uri"] == "", \
        "the Embedded Signup exchange sends redirect_uri='' even on error"
    print("PASS: Meta 400 error propagated, exchange carried redirect_uri=''")


def build_client(get_responses, post_responses):
    """Return an AsyncClient mock recording every request, with separate
    sequences for GET and POST responses. JSON bodies sent to POST are
    recorded in the request log."""
    client = mock.AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    requests_log = []

    get_responses = list(get_responses)
    post_responses = list(post_responses)

    async def fake_get(url, params=None):
        requests_log.append({"method": "GET", "url": url, "params": dict(params or {})})
        return get_responses.pop(0)

    async def fake_post(url, params=None, **kwargs):
        requests_log.append({
            "method": "POST", "url": url, "params": dict(params or {}),
            "json": kwargs.get("json"),
        })
        return post_responses.pop(0)

    client.get.side_effect = fake_get
    client.post.side_effect = fake_post
    return client, requests_log


def test_setup_whatsapp_integration_full_flow():
    """Full Embedded Signup flow using the WABA ID returned by Embedded Signup:
    exchange -> /debug_token validation -> GET /<WABA> (validate) ->
    GET /<WABA>/phone_numbers -> POST /<WABA>/subscribed_apps.

    The WABA ID and phone number ID come ONLY from the Embedded Signup session
    (never /me/businesses or debug_token discovery).
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("y" * 449)
    waba_id = "123456789"          # from Embedded Signup - source of truth
    phone_number_id = "987654321"  # from Embedded Signup - source of truth
    business_id = "biz_999"        # from Embedded Signup

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
            "expires_at": 1893456000,
        }}),
        FakeResponse(200, {"id": waba_id, "name": "My Business"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+15551234567",
            "verified_name": "Verified Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),
    ]

    client, requests_log = build_client(get_responses, post_responses)

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code,
            waba_id=waba_id, phone_number_id=phone_number_id, business_id=business_id,
        ))

    assert ok is True, err
    assert data["access_token"] == "EAA_business_token"
    assert data["waba_id"] == waba_id
    assert data["business_id"] == business_id
    assert data["business_id"] != data["waba_id"]
    assert data["business_name"] == "My Business"
    assert data["phone_number_id"] == phone_number_id
    assert data["display_phone_number"] == "+15551234567"
    assert data["verified_name"] == "Verified Business"

    # 1) Exchange request carries client_id + client_secret + code +
    #    redirect_uri='' (Embedded Signup FB.login popup flow - the canonical
    #    value is what causes 36008)
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == "", \
        "Embedded Signup exchange must send redirect_uri=''"
    assert exchange["params"]["code"] == code

    # 2) Token validated via /debug_token (input_token + app access token)
    dbg = requests_log[1]
    assert dbg["method"] == "GET"
    assert dbg["url"] == f"{GRAPH_BASE}/debug_token"
    assert "input_token" in dbg["params"]

    # 3) WABA validated next: GET /<WABA_ID> with supported fields only
    waba_req = requests_log[2]
    assert waba_req["method"] == "GET"
    assert waba_req["url"] == f"{GRAPH_BASE}/{waba_id}"
    assert waba_req["params"]["fields"] == "id,name"

    # 4) phone_numbers called against the Embedded Signup WABA ID as an EDGE
    #    and NEVER as a fields=phone_numbers lookup
    phone_req = requests_log[3]
    assert phone_req["method"] == "GET"
    assert phone_req["url"] == f"{GRAPH_BASE}/{waba_id}/phone_numbers"
    assert "fields" not in phone_req["params"] or phone_req["params"]["fields"] != "phone_numbers"

    # 5) subscribed_apps POSTed against the same WABA ID
    sub_req = requests_log[4]
    assert sub_req["method"] == "POST"
    assert sub_req["url"] == f"{GRAPH_BASE}/{waba_id}/subscribed_apps"

    # 6) The service must NEVER guess the WABA (no /me/businesses, no /me edge)
    urls = [r["url"] for r in requests_log]
    assert all("/me/businesses" not in u for u in urls), "WABA must NEVER come from /me/businesses"
    assert all("/me" not in u for u in urls), "/me must not be used"
    print("PASS: WABA ID from Embedded Signup used directly; debug_token validation + phone_numbers + subscribed_apps on the WABA edge")


def test_setup_whatsapp_integration_code_only_returns_waba_not_returned():
    """
    Production flow where Meta delivers ONLY the exchangeable code (no session
    asset IDs). The backend exchanges the code and validates the token, but
    because the WA_EMBEDDED_SIGNUP session did not return a WABA ID, it fails
    with a controlled WABA_NOT_RETURNED error. It NEVER falls back to
    /me/businesses or any other discovery mechanism.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("w" * 449)

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
    ]

    client, requests_log = build_client(get_responses, [])

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=None, phone_number_id=None, business_id=None,
        ))

    assert ok is False
    assert data is None
    assert "WABA_NOT_RETURNED" in err, err

    # 1) Exchange carried redirect_uri='' (Embedded Signup popup flow)
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == "", \
        "Embedded Signup exchange must send redirect_uri=''"

    # 2) Token validated via /debug_token
    dbg = requests_log[1]
    assert dbg["url"] == f"{GRAPH_BASE}/debug_token"

    # 3) NO /me/businesses, NO /me, NO discovery edges were called
    urls = [r["url"] for r in requests_log]
    assert all("/me/businesses" not in u for u in urls), "NO /me/businesses fallback allowed"
    assert all("/me" not in u for u in urls), "/me must not be used"
    print("PASS: code-only flow fails with WABA_NOT_RETURNED (no /me/businesses fallback)")


def test_setup_whatsapp_integration_code_only_resolves_ids_server_side():
    """
    Production flow where Meta delivers ONLY the exchangeable code (no
    WA_EMBEDDED_SIGNUP session asset IDs). The backend exchanges the code and
    validates the token via /debug_token, whose granular_scopes target_ids for
    whatsapp_business_management identify the customer's WABA (documented Meta
    fallback - most recently onboarded WABAs appear first). The phone number ID
    is then resolved from the WABA's phone_numbers edge. This mirrors the exact
    scenario that previously stalled the flow after LOGIN_CODE_RECEIVED.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("t" * 449)
    waba_id = "111222333"           # recovered from granular_scopes target_ids
    phone_number_id = "444555666"   # resolved from the WABA phone_numbers edge

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [
                {"scope": "whatsapp_business_management", "target_ids": [waba_id]},
                {"scope": "whatsapp_business_messaging", "target_ids": [waba_id]},
            ],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "Recovered WABA"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+19998887777",
            "verified_name": "Recovered Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),
    ]

    client, requests_log = build_client(get_responses, post_responses)

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=None, phone_number_id=None, business_id=None,
        ))

    assert ok is True, err
    assert data["waba_id"] == waba_id, "WABA must be resolved from granular_scopes target_ids"
    assert data["phone_number_id"] == phone_number_id, "phone number must be resolved from the WABA edge"
    assert data["display_phone_number"] == "+19998887777"
    assert data["business_name"] == "Recovered WABA"

    # 1) Exchange carried redirect_uri='' (Embedded Signup popup flow)
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == "", \
        "Embedded Signup exchange must send redirect_uri=''"

    # 2) Token validated via /debug_token - the WABA is recovered from ITS
    #    granular_scopes target_ids, never from /me/businesses or /me.
    dbg = requests_log[1]
    assert dbg["url"] == f"{GRAPH_BASE}/debug_token"

    # 3) WABA + phone_numbers + subscribed_apps all run against the recovered WABA
    urls = [r["url"] for r in requests_log]
    assert f"{GRAPH_BASE}/{waba_id}" in urls
    assert f"{GRAPH_BASE}/{waba_id}/phone_numbers" in urls
    assert f"{GRAPH_BASE}/{waba_id}/subscribed_apps" in urls
    assert all("/me/businesses" not in u for u in urls), "NO /me/businesses fallback allowed"
    assert all("/me" != u.replace(GRAPH_BASE, "").strip("/") for u in urls), "/me must not be used"
    print("PASS: code-only flow resolves WABA + phone server-side from /debug_token granular_scopes + phone_numbers edge")


def test_setup_whatsapp_integration_missing_phone_number_resolved_server_side():
    """
    WABA present (from the session event) but the session did not return a
    phone number ID. Per the documented Meta server-side fallback the backend
    resolves the phone number ID from the WABA's phone_numbers edge
    (GET /<WABA_ID>/phone_numbers) instead of failing.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("v" * 449)
    waba_id = "123456789"
    resolved_phone = "987654321"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "My Business"}),
        FakeResponse(200, {"data": [{
            "id": resolved_phone,
            "display_phone_number": "+15551234567",
            "verified_name": "Verified Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),
    ]

    client, requests_log = build_client(get_responses, post_responses)

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=waba_id, phone_number_id=None, business_id=None,
        ))

    assert ok is True, err
    assert data["waba_id"] == waba_id
    assert data["phone_number_id"] == resolved_phone
    assert data["display_phone_number"] == "+15551234567"

    urls = [r["url"] for r in requests_log]
    assert all("/me/businesses" not in u for u in urls), "NO /me/businesses fallback allowed"
    assert any(u == f"{GRAPH_BASE}/{waba_id}/phone_numbers" for u in urls), \
        "phone_numbers edge MUST be queried to resolve the missing phone number ID"
    print("PASS: missing phone number ID resolved server-side from the WABA phone_numbers edge")


def test_setup_whatsapp_integration_wrong_app_token_rejected():
    """A token belonging to a different Meta app must be rejected with
    META_PERMISSION_MISSING before any WABA/phone work happens."""
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("u" * 449)
    waba_id = "123456789"
    phone_number_id = "987654321"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "999999999", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging"],
        }}),
    ]

    client, requests_log = build_client(get_responses, [])

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=waba_id, phone_number_id=phone_number_id, business_id=None,
        ))

    assert ok is False
    assert data is None
    assert "META_PERMISSION_MISSING" in err, err
    # Only exchange + debug_token were called - no WABA/phone/subscribe work
    assert len(requests_log) == 2, requests_log
    print("PASS: token from a different app rejected with META_PERMISSION_MISSING")


def test_phone_numbers_edge_regression():
    """
    Regression test: phone_numbers must NEVER be requested as a field, and both
    phone_numbers and subscribed_apps must be called against the WABA ID
    returned by Embedded Signup (never a business ID or a /me id).
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    code = "AQ" + ("z" * 449)
    waba_id = "WABA_A"
    phone_number_id = "PN_1"
    business_id = "BIZ_1"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_t", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "WABA A"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+111",
            "verified_name": "V",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),
    ]

    client, requests_log = build_client(get_responses, post_responses)

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code,
            waba_id=waba_id, phone_number_id=phone_number_id, business_id=business_id,
        ))

    assert ok is True, err
    assert data["waba_id"] == waba_id
    assert data["business_id"] == business_id

    # The exchange (first request) MUST send redirect_uri='' (Embedded Signup
    # popup flow); the other Graph API calls must never include redirect_uri,
    # fields=phone_numbers, /me, or /me/businesses.
    assert requests_log[0]["params"]["redirect_uri"] == "", \
        "Embedded Signup exchange must send redirect_uri=''"
    for req in requests_log[1:]:
        assert "redirect_uri" not in req["params"], f"redirect_uri must not be sent to {req['url']}"
        assert req["params"].get("fields") != "phone_numbers", f"fields=phone_numbers used in {req['url']}"
        assert "/me/businesses" not in req["url"], "/me/businesses must not be used"
        assert "/me" != req["url"].replace(GRAPH_BASE, "").strip("/"), "/me must not be used"

    # debug_token is used ONLY for validation (request 1), never discovery
    assert requests_log[1]["url"] == f"{GRAPH_BASE}/debug_token"
    assert "input_token" in requests_log[1]["params"]

    # WABA is validated next via GET /<WABA_ID>
    assert requests_log[2]["method"] == "GET"
    assert requests_log[2]["url"] == f"{GRAPH_BASE}/{waba_id}"
    # phone_numbers is called only as an edge on the Embedded Signup WABA
    assert requests_log[3]["method"] == "GET"
    assert requests_log[3]["url"] == f"{GRAPH_BASE}/{waba_id}/phone_numbers"
    # subscribed_apps is POSTed to the same WABA
    assert requests_log[4]["method"] == "POST"
    assert requests_log[4]["url"] == f"{GRAPH_BASE}/{waba_id}/subscribed_apps"
    print("PASS: no fields=phone_numbers; WABA validated then phone_numbers + subscribed_apps on the Embedded Signup WABA only")


def test_setup_whatsapp_integration_registers_phone_number():
    """
    After subscribing the WABA, the Tech Provider MUST register the customer's
    business phone number for Cloud API use (Meta "Registering business phone
    numbers" - Embedded Signup does steps 1-3, the Tech Provider still performs
    step 4). The register call is:

        POST /<PHONE_NUMBER_ID>/register
        { "messaging_product": "whatsapp", "pin": "<6-DIGIT-PIN>" }

    The 6-digit PIN comes from META_PHONE_REGISTRATION_PIN (server-side only)
    and must NEVER appear in the request log or be returned to the caller.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("r" * 449)
    waba_id = "123456789"
    phone_number_id = "987654321"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "My Business"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+15551234567",
            "verified_name": "Verified Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),  # subscribed_apps
        FakeResponse(200, {"success": True}),  # register
    ]

    client, requests_log = build_client(get_responses, post_responses)

    # Configure the server-side registration PIN (never the frontend's)
    fake_settings = mock.MagicMock()
    fake_settings.META_PHONE_REGISTRATION_PIN = "481516"

    # Capture the APPLICATION's log output so we can prove the PIN is never
    # written to logs (the outbound request body legitimately contains it).
    import logging
    captured_logs = []
    handler = logging.Handler()
    handler.emit = lambda record: captured_logs.append(record.getMessage())
    logger = logging.getLogger("services.meta_oauth")
    logger.addHandler(handler)
    try:
        with mock.patch("httpx.AsyncClient", return_value=client), \
             mock.patch("services.meta_oauth.get_settings", return_value=fake_settings):
            ok, data, err = run(svc.setup_whatsapp_integration(
                code, waba_id=waba_id, phone_number_id=phone_number_id, business_id=None,
            ))
    finally:
        logger.removeHandler(handler)

    assert ok is True, err
    assert data["phone_registered"] is True

    # 1) subscribe then register - both POSTs against the resolved IDs
    sub_req = requests_log[4]
    assert sub_req["method"] == "POST"
    assert sub_req["url"] == f"{GRAPH_BASE}/{waba_id}/subscribed_apps"

    reg_req = requests_log[5]
    assert reg_req["method"] == "POST"
    assert reg_req["url"] == f"{GRAPH_BASE}/{phone_number_id}/register"
    assert reg_req["json"] == {"messaging_product": "whatsapp", "pin": "481516"}, \
        "register body must carry messaging_product + the 6-digit PIN"

    # 2) the PIN must NEVER be written to application logs or returned to the caller
    assert "481516" not in "\n".join(captured_logs), "the PIN must never be logged"
    assert "481516" not in json.dumps(data), "the PIN must never be returned to the caller"
    print("PASS: phone registered via POST /<PHONE_NUMBER_ID>/register with messaging_product + PIN (never logged/returned)")


def test_setup_registers_already_registered_phone_treated_as_success():
    """
    Meta error 131048 means the number is ALREADY registered for Cloud API use.
    That is a SUCCESS - the number is usable, so the flow must not fail.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("q" * 449)
    waba_id = "123456789"
    phone_number_id = "987654321"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "My Business"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+15551234567",
            "verified_name": "Verified Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),  # subscribed_apps
        FakeResponse(400, {"error": {
            "message": "The phone number is already registered.",
            "type": "GraphMethodException", "code": 131048,
        }}),
    ]

    client, requests_log = build_client(get_responses, post_responses)

    fake_settings = mock.MagicMock()
    fake_settings.META_PHONE_REGISTRATION_PIN = "112233"

    with mock.patch("httpx.AsyncClient", return_value=client), \
         mock.patch("services.meta_oauth.get_settings", return_value=fake_settings):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=waba_id, phone_number_id=phone_number_id, business_id=None,
        ))

    assert ok is True, err
    assert data["phone_registered"] is True, "an already-registered number must be treated as success"
    print("PASS: already-registered phone (Meta 131048) treated as success")


def test_setup_skips_registration_when_pin_not_configured():
    """
    Without META_PHONE_REGISTRATION_PIN the registration step is skipped
    (not a hard failure) and the rest of the flow still completes.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("p" * 449)
    waba_id = "123456789"
    phone_number_id = "987654321"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        FakeResponse(200, {"data": {
            "app_id": "3862862217342382", "type": "BUSINESS",
            "scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
            "granular_scopes": [],
        }}),
        FakeResponse(200, {"id": waba_id, "name": "My Business"}),
        FakeResponse(200, {"data": [{
            "id": phone_number_id,
            "display_phone_number": "+15551234567",
            "verified_name": "Verified Business",
        }]}),
    ]
    post_responses = [
        FakeResponse(200, {"success": True}),  # subscribed_apps only - no register call
    ]

    client, requests_log = build_client(get_responses, post_responses)

    fake_settings = mock.MagicMock()
    fake_settings.META_PHONE_REGISTRATION_PIN = ""

    with mock.patch("httpx.AsyncClient", return_value=client), \
         mock.patch("services.meta_oauth.get_settings", return_value=fake_settings):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code, waba_id=waba_id, phone_number_id=phone_number_id, business_id=None,
        ))

    assert ok is True, err
    assert data["phone_registered"] is False
    assert all("/register" not in r["url"] for r in requests_log), \
        "register must be skipped when no PIN is configured"
    print("PASS: phone registration skipped (no PIN configured) without failing the flow")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"==> {name}")
            fn()
    print("\nALL MOCK TESTS PASSED")
