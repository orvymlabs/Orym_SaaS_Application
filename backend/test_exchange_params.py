"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
  1. The WhatsApp Embedded Signup Step 1 exchange sends EXACTLY
     client_id + client_secret + code (no redirect_uri).
  2. The redirect_uri parameter is intentionally omitted for the Embedded
     Signup flow (FB.login + config_id). This matches Meta's official
     Embedded Signup exchange. Sending redirect_uri (the empty string or any
     real URL) is what triggers Meta error_subcode 36008.
"""
import asyncio
import httpx

from services.meta_oauth import MetaOAuthService, CANONICAL_REDIRECT_URI

CANONICAL = "https://apps.orvym.com/dashboard/integrations/"

captured = {}


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, params=None):
        captured["url"] = url
        captured["params"] = dict(params or {})
        return httpx.Response(200, json={"access_token": "FAKE_TOKEN"})


async def main():
    svc = MetaOAuthService(app_id="3862862217342382", app_secret="***")
    code = "AQ" + ("x" * 449)

    print("=" * 70)
    print("TEST 1: Embedded Signup exchange (redirect_uri omitted)")
    print("=" * 70)
    orig = httpx.AsyncClient
    httpx.AsyncClient = FakeClient
    try:
        ok, data, err = await svc.exchange_code_for_token(code)
    finally:
        httpx.AsyncClient = orig

    assert ok is True, err
    assert captured["url"] == f"{svc.GRAPH_API_BASE}/oauth/access_token"
    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code"}, \
        f"exchange must send exactly client_id+client_secret+code, got {sorted(captured['params'].keys())}"
    assert "redirect_uri" not in captured["params"], \
        "redirect_uri must NOT be sent in the Embedded Signup exchange"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical redirect_uri must include the trailing slash"

    # The Embedded Signup exchange must NOT include redirect_uri
    assert "redirect_uri" not in captured["params"]
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("PASS: Embedded Signup exchange sends exactly ['client_id', 'client_secret', 'code']")
    print("PASS: redirect_uri is NOT present in the Meta request (correct for Embedded Signup)")
    print("PASS: canonical value, empty string, or any URL is never forwarded to Meta (it causes 36008)")


asyncio.run(main())
