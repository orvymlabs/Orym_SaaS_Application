"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
 1. The Embedded Signup token exchange sends ONLY client_id + client_secret +
    code to Meta - redirect_uri is NEVER included.
 2. redirect_uri is never appended even when a value is passed to the service.
 3. No empty-string redirect_uri assignment exists anywhere in the service code.
"""
import asyncio
import json
from unittest import mock

from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_exchange_sends_only_client_credentials_and_code():
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")
    code = "AQ" + ("x" * 449)

    client = mock.AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    async def fake_get(url, params=None):
        captured["url"] = url
        captured["params"] = dict(params or {})
        return FakeResponse(200, {"access_token": "EAA_t", "token_type": "bearer"})

    client.get.side_effect = fake_get

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.exchange_code_for_token(code))

    assert ok is True, err
    assert captured["url"] == "https://graph.facebook.com/v26.0/oauth/access_token"
    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code"}, \
        f"exchange must send ONLY client_id + client_secret + code, got {sorted(captured['params'])}"
    assert "redirect_uri" not in captured["params"], "redirect_uri must NOT be sent"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code
    print("PASS: exchange sends ONLY client_id + client_secret + code (no redirect_uri)")


def test_exchange_never_appends_passed_redirect_uri():
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")

    client = mock.AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    async def fake_get(url, params=None):
        captured["params"] = dict(params or {})
        return FakeResponse(200, {"access_token": "EAA_t", "token_type": "bearer"})

    client.get.side_effect = fake_get

    with mock.patch("httpx.AsyncClient", return_value=client):
        ok, data, err = run(svc.exchange_code_for_token("AQcode", redirect_uri=CANONICAL))

    assert ok is True, err
    assert "redirect_uri" not in captured["params"], \
        "passed redirect_uri must be ignored - never sent to Meta"
    print("PASS: passed redirect_uri is ignored - exchange never sends it")


def test_no_empty_string_or_canonical_redirect_uri_in_exchange_code():
    source = open("services/meta_oauth.py").read()

    # The exchange params dict must not carry redirect_uri at all.
    assert '"redirect_uri": redirect_uri' not in source, \
        "exchange must not build params with redirect_uri"
    assert '"redirect_uri": ""' not in source, "dict-literal empty string banned"
    assert "params['redirect_uri'] = ''" not in source, "empty-string assignment banned"
    assert 'redirect_uri=""' not in source.replace("NEVER send redirect_uri=\"\"", "")

    # The canonical constant is still defined for the OAuth dialog / other flows.
    assert CANONICAL_REDIRECT_URI == CANONICAL
    print("PASS: exchange code never constructs redirect_uri params; canonical constant preserved")


if __name__ == "__main__":
    test_exchange_sends_only_client_credentials_and_code()
    test_exchange_never_appends_passed_redirect_uri()
    test_no_empty_string_or_canonical_redirect_uri_in_exchange_code()
    print("\nALL EXCHANGE-PARAMS TESTS PASSED")
