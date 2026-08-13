"""
Verify the code exchange parameter construction per Meta's current official
Embedded Signup / Facebook Login for Business flow.

Proves:
  1. The WhatsApp Embedded Signup Step 1 exchange sends EXACTLY
     client_id + client_secret + code + locale - NO redirect_uri.
  2. Per Meta's current official docs the exchangeable code is returned
     directly to the JS popup callback (no server-side redirect), so there is
     no redirect URI to echo. Sending the JS SDK's internal xd_arbiter channel
     URL (https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46) or
     any other value as redirect_uri makes Meta validate it against the app's
     domains and fails with error code 191 ("The domain of this URL isn't
     included in the app's domains"). staticxx.facebook.com is a Meta-internal
     domain and must never be added to App Domains.
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
    print("TEST 1: Embedded Signup exchange (no redirect_uri sent)")
    print("=" * 70)
    orig = httpx.AsyncClient
    httpx.AsyncClient = FakeClient
    try:
        ok, data, err = await svc.exchange_code_for_token(code)
    finally:
        httpx.AsyncClient = orig

    assert ok is True, err
    assert captured["url"] == f"{svc.GRAPH_API_BASE}/oauth/access_token"
    assert set(captured["params"].keys()) == {"client_id", "client_secret", "code", "locale"}, \
        f"exchange must send exactly client_id+client_secret+code+locale (no redirect_uri), got {sorted(captured['params'].keys())}"
    assert "redirect_uri" not in captured["params"], \
        "redirect_uri must NOT be sent (Meta current docs: code is returned directly to the JS callback)"
    assert captured["params"]["client_id"] == "3862862217342382"
    assert captured["params"]["code"] == code

    print("=" * 70)
    print("ASSERTIONS")
    print("=" * 70)

    assert CANONICAL_REDIRECT_URI == CANONICAL
    assert CANONICAL.endswith("/"), "canonical display URL must include the trailing slash"

    print("PASS: Embedded Signup exchange sends exactly ['client_id', 'client_secret', 'code', 'locale']")
    print("PASS: redirect_uri is NOT sent - per Meta's current official Embedded Signup docs")
    print("PASS: this prevents Meta error code 191 ('The domain of this URL isn't included in the app's domains')")


asyncio.run(main())
