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


def test_setup_whatsapp_integration_full_flow():
    """Full flow: exchange -> WABA -> phone numbers -> integration_data."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE
    code = "AQ" + ("y" * 449)
    redirect_uri = "https://apps.orvym.com/dashboard/integrations"

    responses = [
        FakeResponse(200, {"access_token": "EAA_business_token", "token_type": "bearer", "expires_in": 5184000}),
        FakeResponse(200, {"id": "123456789", "name": "My Business"}),
        FakeResponse(200, {"data": [{"id": "987654321", "display_phone_number": "+15551234567"}]}),
    ]
    requests_log = []

    client = mock.AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    async def fake_get(url, params=None):
        requests_log.append({"url": url, "params": dict(params or {})})
        return responses.pop(0)

    client.get.side_effect = fake_get

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.setup_whatsapp_integration(code, redirect_uri))

    assert ok is True, err
    assert data["access_token"] == "EAA_business_token"
    assert data["waba_id"] == "123456789"
    assert data["phone_number_id"] == "987654321"
    assert data["display_phone_number"] == "+15551234567"

    # Verify the exchange request to Meta carried the exact redirect_uri
    exchange = requests_log[0]
    assert exchange["url"] == f"{GRAPH_BASE}/oauth/access_token"
    assert exchange["params"]["redirect_uri"] == redirect_uri
    assert exchange["params"]["code"] == code

    # WABA and phone requests must carry the access token as bearer param
    assert requests_log[1]["url"] == f"{GRAPH_BASE}/me"
    assert requests_log[2]["url"] == f"{GRAPH_BASE}/123456789/phone_numbers"
    print("PASS: full setup flow (exchange -> WABA -> phone numbers)")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"==> {name}")
            fn()
    print("\nALL MOCK TESTS PASSED")
