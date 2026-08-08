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


def test_exchange_with_redirect_uri_forwards_exact_value():
    """The EXACT dialog redirect_uri must appear in the Meta request."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("x" * 449)
    redirect_uri = "https://apps.orvym.com/dashboard/integrations"

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer", "expires_in": 5184000}
    )):
        ok, data, err = run(svc.exchange_code_for_token(code, redirect_uri))

    assert ok is True, err
    assert data["access_token"] == "EAA_token"
    assert captured["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["client_secret"] == "secret"
    assert captured["params"]["code"] == code
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations"
    assert captured["params"]["redirect_uri"] != ""
    print("PASS: exact redirect_uri forwarded to Meta")


def test_exchange_without_redirect_uri_omits_it():
    """When no redirect_uri is supplied it must be OMITTED, never empty."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode"))

    assert ok is True, err
    assert "redirect_uri" not in captured["params"], "redirect_uri must be OMITTED"
    print("PASS: redirect_uri omitted entirely when not supplied")


def test_exchange_never_sends_empty_string():
    """redirect_uri='' must NEVER be present in the request (even as empty)."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    # Passing empty string is treated as "no value" -> omitted
    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(svc.exchange_code_for_token("AQcode", ""))

    assert ok is True, err
    assert "redirect_uri" not in captured["params"]
    print("PASS: empty string redirect_uri is never sent")


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
        ok, data, err = run(svc.exchange_code_for_token("AQcode", "https://apps.orvym.com/dashboard/integrations"))

    assert ok is False
    assert data is None
    assert "redirect_uri is identical" in err
    assert captured["params"]["redirect_uri"] == "https://apps.orvym.com/dashboard/integrations"
    print("PASS: Meta 400 error propagated with redirect_uri intact")


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
    redirect_uri = "https://apps.orvym.com/dashboard/integrations/"
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
            code, redirect_uri,
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

    # 1) Exchange request carried the exact redirect_uri
    exchange = requests_log[0]
    assert exchange["method"] == "GET"
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == redirect_uri
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
            code, None,
            waba_id=waba_id, phone_number_id=phone_number_id, business_id=business_id,
        ))

    assert ok is True, err
    assert data["waba_id"] == waba_id
    assert data["business_id"] == business_id

    # No request may ever use fields=phone_numbers, /me, or debug_token
    for req in requests_log:
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
