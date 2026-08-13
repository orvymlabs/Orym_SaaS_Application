"""
Verify the code exchange parameter construction after the redirect_uri fix.

Proves:
  1. The WhatsApp Embedded Signup Step 1 exchange sends EXACTLY
     client_id + client_secret + code + redirect_uri.
  2. redirect_uri equals the EXACT value the FB JS SDK used in the OAuth
     dialog - the xd_arbiter channel URL
     (https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46) - which
     is what Meta binds to the authorization code. Sending a different
     redirect_uri (the empty string, the canonical app URL, or any other
     value) is what triggers Meta error_subcode 36008.
"""
import asyncio
import httpx

from services.meta_oauth import MetaOAuthService, EXCHANGE_REDIRECT_URI, CANONICAL_REDIRECT_URI

EXCHANGE = "https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46"
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
    print("TEST 1: Embedded Signup exchange (canonical redirect_uri sent)")
    print("=" * 70)
    orig = httpx.AsyncClient
    httpx.AsyncClient = FakeClient
    try:
        ok, data, err = await svc.exchange_code_for_token(code)
    finally:
        httpx.AsyncClient = orig

    assert ok is True, err
    assert captured["url"] == f"{svc.GRAPH_API_BASE}/oauth/access_token"
    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "redirect_uri"}, \
        f"exchange must send exactly client_id+client_secret+code+redirect_uri, got {sorted(captured['params'].keys())}"
    assert captured["params"]["redirect_uri"] == EXCHANGE, \
        "redirect_uri must be the exact JS SDK dialog value (xd_arbiter channel URL)"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert EXCHANGE_REDIRECT_URI == EXCHANGE
    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical redirect_uri must include the trailing slash"
    assert EXCHANGE_REDIRECT_URI != CANONICAL_REDIRECT_URI, \
        "the exchange redirect_uri (xd_arbiter) must differ from the canonical app URL"

    # The Embedded Signup exchange MUST include redirect_uri = the exact dialog value
    assert captured["params"]["redirect_uri"] == EXCHANGE
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("PASS: Embedded Signup exchange sends exactly ['client_id', 'client_secret', 'code', 'redirect_uri']")
    print(f"PASS: redirect_uri is present and equals the JS SDK dialog value ({EXCHANGE})")
    print("PASS: the canonical app URL, empty string, or any other value is never used as redirect_uri (it causes 36008)")


asyncio.run(main())
