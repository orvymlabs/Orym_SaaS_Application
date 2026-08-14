"""
Test script to verify OAuth token exchange parameters for the WhatsApp
Embedded Signup FB.login popup flow.

Rule (Meta's current official Embedded Signup / Facebook Login for Business
docs): the exchange sends client_id + client_secret + code ONLY - NO
redirect_uri. The exchangeable code is returned directly to the JS popup
callback (no server-side redirect), so there is no redirect URI to echo.
Sending the JS SDK's internal xd_arbiter channel URL
(https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46) or any other
value as redirect_uri makes Meta validate it against the app's domains and
fails with error code 191 ("The domain of this URL isn't included in the
app's domains"). staticxx.facebook.com is a Meta-internal domain and must
never be added to App Domains.

This script exercises the REAL service method (exchange_code_for_token) with a
mocked httpx client and verifies the exact parameters Meta receives.
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
    print(f"redirect_uri present: {'redirect_uri' in captured['params']}  (should be False)")
    print(f"Parameter names: {sorted(captured['params'].keys())}")
    print()

    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "locale"}, \
        "exchange must send exactly client_id + client_secret + code + locale (no redirect_uri)"
    assert "redirect_uri" not in captured["params"], \
        "redirect_uri must NOT be sent (Meta current docs: code is returned directly to the JS callback)"
    print("PASS: exchange sends exactly client_id + client_secret + code + locale (no redirect_uri)")
    print()

    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("✓ The exchange sends client_id + client_secret + code + locale ONLY")
    print("✓ No redirect_uri is sent - per Meta's current official Embedded Signup docs")
    print("✓ This prevents error code 191 ('The domain of this URL isn't included in the app's domains')")
    print("=" * 80)


if __name__ == "__main__":
    test_token_exchange_params()
