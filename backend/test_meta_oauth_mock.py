"""
Comprehensive mock-based tests for MetaOAuthService.exchange_code_for_token.

These tests verify the EXACT HTTP request the backend sends to Meta:
  - endpoint URL
  - query parameters
  - redirect_uri forwarding (exact value, never empty string)
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


def test_exchange_always_sends_canonical_redirect_uri():
    """
    The exchange ALWAYS sends redirect_uri. When invoked WITHOUT an explicit
    redirect_uri (or with an empty one) the canonical production value is
    used - never omitted, never an empty string, never null. Omitting it is
    exactly what triggers Meta error_subcode 36008.
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
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "canonical redirect_uri must ALWAYS be sent"
    print("PASS: exchange always sends the canonical redirect_uri (never omitted)")

    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "redirect_uri"}


def test_exchange_without_redirect_uri_uses_canonical():
    """When no redirect_uri is supplied the exchange uses the canonical value."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode"))

    assert ok is True, err
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/"
    print("PASS: redirect_uri falls back to the canonical production value")


def test_exchange_forwards_exact_redirect_uri():
    """
    An explicit redirect_uri is forwarded verbatim (byte-for-byte) to Meta's
    "redirect_uri identical" check. The canonical value
    (https://apps.orvym.com/dashboard/integrations/) is what production sends.
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
    assert captured["params"]["redirect_uri"] == redirect_uri, \
        "redirect_uri must be forwarded byte-identically"
    print("PASS: exact redirect_uri forwarded to Meta")


def test_exchange_empty_string_redirect_uri_uses_canonical():
    """redirect_uri="" must NEVER be sent - the canonical value is used instead."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode", redirect_uri="   "))

    assert ok is True, err
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "empty/whitespace redirect_uri must fall back to the canonical value"
    print("PASS: empty-string redirect_uri is never sent - canonical value used")


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
    assert "redirect_uri is identical" in err
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "the canonical redirect_uri is always sent, even on error"
    print("PASS: Meta 400 error propagated, exchange still carried the canonical redirect_uri")


def build_client(get_responses, post_responses):
    """Return an AsyncClient mock recording every request, with separate
    sequences for GET and POST responses."""
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
        requests_log.append({"method": "POST", "url": url, "params": dict(params or {})})
        return post_responses.pop(0)

    client.get.side_effect = fake_get
    client.post.side_effect = fake_post
    return client, requests_log


def test_setup_whatsapp_integration_full_flow():
    """Full Embedded Signup flow using the WABA ID returned by Embedded Signup:
    exchange -> GET /<WABA> (validate) -> GET /<WABA>/phone_numbers -> POST /<WABA>/subscribed_apps.

    The WABA ID is NEVER guessed/discovered from the token (no debug_token call).
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("y" * 449)
    waba_id = "123456789"          # from Embedded Signup - source of truth
    phone_number_id = "987654321"  # from Embedded Signup - source of truth
    business_id = "biz_999"        # from Embedded Signup

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
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

    # 1) Exchange request carries client_id + client_secret + code + the
    #    canonical redirect_uri (https://apps.orvym.com/dashboard/integrations/)
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "canonical redirect_uri must ALWAYS be sent in the exchange"
    assert exchange["params"]["code"] == code

    # 2) WABA validated first: GET /<WABA_ID> with supported fields only
    waba_req = requests_log[1]
    assert waba_req["method"] == "GET"
    assert waba_req["url"] == f"{GRAPH_BASE}/{waba_id}"
    assert waba_req["params"]["fields"] == "id,name"

    # 3) phone_numbers called against the Embedded Signup WABA ID as an EDGE
    #    and NEVER as a fields=phone_numbers lookup
    phone_req = requests_log[2]
    assert phone_req["method"] == "GET"
    assert phone_req["url"] == f"{GRAPH_BASE}/{waba_id}/phone_numbers"
    assert "fields" not in phone_req["params"] or phone_req["params"]["fields"] != "phone_numbers"

    # 4) subscribed_apps POSTed against the same WABA ID
    sub_req = requests_log[3]
    assert sub_req["method"] == "POST"
    assert sub_req["url"] == f"{GRAPH_BASE}/{waba_id}/subscribed_apps"

    # 5) The service must NEVER guess the WABA (no debug_token, no /me)
    urls = [r["url"] for r in requests_log]
    assert all("/debug_token" not in u for u in urls), "WABA must come from Embedded Signup, never debug_token"
    assert all("/me" not in u for u in urls), "/me must not be used"
    print("PASS: WABA ID from Embedded Signup used directly; phone_numbers + subscribed_apps on the WABA edge")


def test_setup_whatsapp_integration_code_only_discovery():
    """
    Production flow: Meta delivers ONLY the exchangeable code (the OAuth
    redirect back carries no waba_id / phone_number_id / business_id). The
    backend must exchange the code and then discover the WABA server-side via
    Meta's documented business portfolio edges: GET /me/businesses -> the
    business portfolio, then GET /<business_id>/client_whatsapp_business_accounts
    -> the WABA IDs shared with the portfolio. debug_token is never used.
    """
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("w" * 449)
    discovered_business_id = "biz_portfolio_123"
    discovered_waba_id = "111222333"
    discovered_phone_id = "444555666"

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
        # GET /me/businesses - the documented Business edge resolving the
        # business portfolio(s) the token can access
        FakeResponse(200, {"data": [{"id": discovered_business_id, "name": "Portfolio Co"}]}),
        # GET /<business_id>/client_whatsapp_business_accounts - the
        # documented "Get list of shared WABAs" edge for Embedded Signup
        FakeResponse(200, {"data": [{"id": discovered_waba_id, "name": "Discovered Business"}]}),
        FakeResponse(200, {"id": discovered_waba_id, "name": "Discovered Business"}),
        FakeResponse(200, {"data": [{
            "id": discovered_phone_id,
            "display_phone_number": "+19998887777",
            "verified_name": "Discovered Verified",
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
    assert data["access_token"] == "EAA_business_token"
    assert data["waba_id"] == discovered_waba_id
    assert data["phone_number_id"] == discovered_phone_id
    assert data["display_phone_number"] == "+19998887777"
    assert data["verified_name"] == "Discovered Verified"
    assert data["business_name"] == "Discovered Business"
    # business_id falls back to the genuine portfolio resolved from
    # /me/businesses (never fabricated)
    assert data["business_id"] == discovered_business_id
    assert data["business_id"] != data["waba_id"]

    # 1) Exchange request carries client_id + client_secret + code + the
    #    canonical redirect_uri (never omitted, never empty)
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "canonical redirect_uri must ALWAYS be sent in the exchange"

    # 2) Business portfolio resolved via GET /me/businesses (fields=id,name)
    biz_req = requests_log[1]
    assert biz_req["method"] == "GET"
    assert biz_req["url"] == f"{GRAPH_BASE}/me/businesses"
    assert biz_req["params"]["fields"] == "id,name"
    assert biz_req["params"]["access_token"] == "EAA_business_token"

    # 3) WABA discovered via the client_whatsapp_business_accounts edge of the
    #    resolved business portfolio (fields=id,name)
    client_waba_req = requests_log[2]
    assert client_waba_req["method"] == "GET"
    assert client_waba_req["url"] == f"{GRAPH_BASE}/{discovered_business_id}/client_whatsapp_business_accounts"
    assert client_waba_req["params"]["fields"] == "id,name"

    # 4) WABA validated via GET /<WABA_ID>
    waba_req = requests_log[3]
    assert waba_req["method"] == "GET"
    assert waba_req["url"] == f"{GRAPH_BASE}/{discovered_waba_id}"
    assert waba_req["params"]["fields"] == "id,name"

    # 5) phone_numbers as an edge on the discovered WABA (never fields=phone_numbers)
    phone_req = requests_log[4]
    assert phone_req["method"] == "GET"
    assert phone_req["url"] == f"{GRAPH_BASE}/{discovered_waba_id}/phone_numbers"

    # 6) subscribed_apps POSTed against the discovered WABA
    sub_req = requests_log[5]
    assert sub_req["method"] == "POST"
    assert sub_req["url"] == f"{GRAPH_BASE}/{discovered_waba_id}/subscribed_apps"

    # debug_token must NEVER be used for WABA discovery
    urls = [r["url"] for r in requests_log]
    assert all("/debug_token" not in u for u in urls), "WABA must never be discovered via debug_token"
    print("PASS: code-only flow - WABA discovered via /me/businesses + client_whatsapp_business_accounts; phone_numbers + subscribed_apps on the discovered WABA")


def test_setup_whatsapp_integration_code_only_no_waba():
    """Code-only flow where the business edges return no WABA IDs must fail clearly."""
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("v" * 449)

    get_responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer"}),
        # Portfolio resolves, but the WABA edges return nothing
        FakeResponse(200, {"data": [{"id": "biz_portfolio_123", "name": "Portfolio Co"}]}),
        FakeResponse(200, {"data": []}),  # client_whatsapp_business_accounts
        FakeResponse(200, {"data": []}),  # owned_whatsapp_business_accounts
    ]

    client, _ = build_client(get_responses, [])

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(
            code,
        ))

    assert ok is False
    assert data is None
    assert "No WhatsApp Business Account found" in err
    print("PASS: code-only flow with no discoverable WABA fails with clear error")


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

    # The exchange (first request) MUST carry the canonical redirect_uri; the
    # other Graph API calls must never include redirect_uri, fields=phone_numbers,
    # /me, or debug_token.
    assert requests_log[0]["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations/", \
        "canonical redirect_uri must ALWAYS be sent in the exchange"
    for req in requests_log[1:]:
        assert "redirect_uri" not in req["params"], f"redirect_uri must not be sent to {req['url']}"
        assert req["params"].get("fields") != "phone_numbers", f"fields=phone_numbers used in {req['url']}"
        assert "/me" != req["url"].replace(GRAPH_BASE, "").strip("/"), "/me must not be used"
        assert "/debug_token" not in req["url"], "WABA must never be discovered via debug_token"

    # WABA is validated first via GET /<WABA_ID>
    assert requests_log[1]["method"] == "GET"
    assert requests_log[1]["url"] == f"{GRAPH_BASE}/{waba_id}"
    # phone_numbers is called only as an edge on the Embedded Signup WABA
    assert requests_log[2]["method"] == "GET"
    assert requests_log[2]["url"] == f"{GRAPH_BASE}/{waba_id}/phone_numbers"
    # subscribed_apps is POSTed to the same WABA
    assert requests_log[3]["method"] == "POST"
    assert requests_log[3]["url"] == f"{GRAPH_BASE}/{waba_id}/subscribed_apps"
    print("PASS: no fields=phone_numbers; WABA validated then phone_numbers + subscribed_apps on the Embedded Signup WABA only")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"==> {name}")
            fn()
    print("\nALL MOCK TESTS PASSED")
