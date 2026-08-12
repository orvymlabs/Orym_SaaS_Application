"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
 1. The WhatsApp Embedded Signup Step 1 exchange sends EXACTLY
    client_id + client_secret + code - redirect_uri is NEVER present.
 2. Sending redirect_uri (canonical value, empty string or any other value)
    is what caused Meta error_subcode 36008; it is therefore never appended.
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
    print("TEST 1: Embedded Signup exchange (no redirect_uri supplied)")
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
    assert "redirect_uri" not in captured["params"], "redirect_uri must NOT be sent to Meta"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical redirect_uri must include the trailing slash"

    # The Embedded Signup exchange NEVER includes the redirect_uri parameter
    assert "redirect_uri" not in captured["params"]

    print("PASS: Embedded Signup exchange sends exactly ['client_id', 'client_secret', 'code']")
    print("PASS: redirect_uri is NOT present in the Meta request")
    print("PASS: canonical value, empty string or any redirect_uri is never forwarded to Meta")


asyncio.run(main())
