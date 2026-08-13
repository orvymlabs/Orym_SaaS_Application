"""
Test script to verify OAuth token exchange parameters for the WhatsApp
Embedded Signup FB.login popup flow.

Rule: the Embedded Signup (Facebook Login for Business config_id) exchange
sends client_id + client_secret + code + redirect_uri. redirect_uri MUST be
the EXACT value the FB JS SDK used in the OAuth dialog - the xd_arbiter
channel URL (https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46) -
which is what Meta binds to the authorization code. Sending a different
redirect_uri - the empty string, the canonical
https://apps.orvym.com/dashboard/integrations/, or any other value - is
exactly what triggers Meta error_subcode 36008 ("make sure your redirect_uri
is identical to the one you used in the OAuth dialog request").

This script exercises the REAL service method (exchange_code_for_token) with a
mocked httpx client and verifies the exact parameters Meta receives.
"""
import asyncio
import json
from unittest import mock

from services.meta_oauth import MetaOAuthService, EXCHANGE_REDIRECT_URI

GRAPH_BASE = "https://graph.facebook.com/v26.0"
EXPECTED_EXCHANGE_REDIRECT_URI = "https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46"


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


def captured_request(captured, status_code, payload):
    client = mock.AsyncMock()
    response = FakeResponse(status_code, payload)
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


def test_token_exchange_params():
    """Test what parameters are actually constructed for token exchange"""
    service = MetaOAuthService(app_id="test_app_id_123", app_secret="test_secret_456")
    service.GRAPH_API_BASE = GRAPH_BASE
    test_code = "test_authorization_code_from_dialog"

    captured = {}
    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"access_token": "EAA_token", "token_type": "bearer"}
    )):
        ok, data, err = run(service.exchange_code_for_token(test_code))

    assert ok is True, err
    assert captured["url"] == f"{GRAPH_BASE}/oauth/access_token"

    print("=" * 80)
    print("TEST: Token Exchange Parameter Construction")
    print("=" * 80)
    print()
    print("Parameters that will be sent to Meta:")
    for key, value in captured["params"].items():
        print(f"  {key}: '{value}'")
    print()
    print(f"redirect_uri present: {'redirect_uri' in captured['params']}  (should be True)")
    print(f"redirect_uri value: {captured['params'].get('redirect_uri')}")
    print(f"Parameter names: {sorted(captured['params'].keys())}")
    print()

    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "redirect_uri"}, \
        "exchange must send exactly client_id + client_secret + code + redirect_uri"
    assert captured["params"]["redirect_uri"] == EXPECTED_EXCHANGE_REDIRECT_URI, \
        "redirect_uri must be the exact JS SDK dialog value (xd_arbiter channel URL)"
    assert EXCHANGE_REDIRECT_URI == EXPECTED_EXCHANGE_REDIRECT_URI
    print("PASS: exchange sends exactly client_id + client_secret + code + the exact dialog redirect_uri")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ The exchange sends client_id + client_secret + code + redirect_uri")
    print(f"✓ redirect_uri = {EXPECTED_EXCHANGE_REDIRECT_URI}")
    print("✓ This is the exact value the JS SDK used in the OAuth dialog, so Meta")
    print("  binds the code to it and the exchange matches (prevents error_subcode 36008)")
    print("=" * 80)


if __name__ == "__main__":
    test_token_exchange_params()
