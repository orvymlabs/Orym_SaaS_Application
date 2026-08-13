"""
Mock-based tests for the Meta app credential verification added to
MetaOAuthService (used by GET /api/integrations/meta/verify) and for the
actionable 36008 hint surfaced from exchange errors.

They mock httpx.AsyncClient so no real network call is made.
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
    """Return an AsyncClient mock that records the request it received."""
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


def test_verify_app_credentials_success():
    """
    GET /v26.0/<APP_ID> with an <APP_ID>|<APP_SECRET> app access token must
    return the app name when the secret is valid. The secret is only used to
    build the app token and is never returned.
    """
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 200, {"id": "3862862217342382", "name": "ORVYM SaaS"}
    )):
        ok, data, err = run(svc.verify_app_credentials())

    assert ok is True, err
    assert data["app_name"] == "ORVYM SaaS"
    assert data["graph_version_supported"] is True
    assert captured["url"] == f"{GRAPH_BASE}/3862862217342382"
    assert captured["params"]["fields"] == "id,name"
    assert captured["params"]["access_token"] == "3862862217342382|secret"
    print("PASS: app credentials verified via GET /<APP_ID> with app access token")


def test_verify_app_credentials_invalid_secret():
    """An invalid app secret must be reported as a failed check (not a version failure)."""
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="wrong-secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    error_payload = {
        "error": {
            "message": "Error validating access token: Session has expired on Thursday, 01-Jan-15 00:00:00 PST.",
            "type": "OAuthException", "code": 190, "error_subcode": 463,
        }
    }

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 400, error_payload
    )):
        ok, data, err = run(svc.verify_app_credentials())

    assert ok is False
    assert data["graph_version_supported"] is True, "secret failure is not a version failure"
    assert data["app_name"] is None
    assert "validating access token" in err
    print("PASS: invalid app secret detected as a credential failure, version still valid")


def test_verify_app_credentials_unsupported_version():
    """
    A Graph version error (code 12, "Unsupported get request ... documented
    versions") must be reported as a version failure so the verify endpoint can
    flag an incorrectly configured Graph API version.
    """
    captured = {}
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="secret")
    svc.GRAPH_API_BASE = GRAPH_BASE

    error_payload = {
        "error": {
            "message": "Unsupported get request. Please use one of the documented versions: v21.0, v22.0, v23.0, v24.0, v25.0, v26.0",
            "type": "GraphMethodException", "code": 12, "error_subcode": None,
        }
    }

    with mock.patch("httpx.AsyncClient", return_value=captured_request(
        captured, 400, error_payload
    )):
        ok, data, err = run(svc.verify_app_credentials())

    assert ok is False
    assert data["graph_version_supported"] is False
    print("PASS: unsupported Graph API version detected")


def test_exchange_36008_error_includes_actionable_hint():
    """
    When Meta returns error_subcode 36008 the surfaced error is the
    CLAUDE.md-approved user-facing message (never suggesting changing
    redirect_uri) and the exchange sends redirect_uri = the EXACT value the JS
    SDK used in the OAuth dialog (the xd_arbiter channel URL - the value Meta
    binds to the code). A 36008 with the correct redirect_uri means the code
    itself was consumed, expired or issued outside the config_id popup flow.
    """
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
        ok, data, err = run(svc.exchange_code_for_token("AQ" + "x" * 449))

    assert ok is False
    assert "OAUTH_REDIRECT_URI_MISMATCH" in err
    assert "Please restart WhatsApp Embedded Signup" in err
    assert "add redirect_uri" not in err.lower()
    # The Embedded Signup exchange sends redirect_uri = the exact dialog value
    assert captured["params"]["redirect_uri"] == EXPECTED_EXCHANGE_REDIRECT_URI
    assert EXCHANGE_REDIRECT_URI == EXPECTED_EXCHANGE_REDIRECT_URI
    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "redirect_uri"}
    print("PASS: 36008 surfaces the approved message; exchange sent the exact dialog redirect_uri")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"==> {name}")
            fn()
    print("\nALL VERIFY TESTS PASSED")
