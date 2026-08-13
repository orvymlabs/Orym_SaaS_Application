"""
Meta Embedded Signup fresh-code exchange probe.

Implements CLAUDE.md "SIXTH: TEST WITH A FRESH CODE": given a brand-new
exchangeable code, perform EXACTLY ONE backend token exchange (identical to
production: GET /oauth/access_token with client_id + client_secret + code -
NO redirect_uri, the official Embedded Signup exchange) and capture Meta's
actual response.

Also runs a production-parity check that compares the DEPLOYED
/openapi.json against the expected callback shape, so a stale build can never
masquerade as the current code.

Usage (run from backend/):
    python probe_meta_exchange.py --code AQ<your-fresh-code>

Options:
    --code <CODE>            The fresh exchangeable code from a NEW Embedded
                             Signup run. Never reuse an old code.
    --production-url <URL>   Default: https://orym-saas-application.onrender.com
    --skip-parity-check      Skip the deployed-openapi parity check.
    --api-version <vNN.N>    Override the Graph API version (default: v26.0).

The app secret is NEVER printed. Codes and tokens are printed masked.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

BACKEND_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BACKEND_DIR))

from services.meta_oauth import MetaOAuthService  # noqa: E402

EXPECTED_CALLBACK_PATH = "/api/integrations/meta/oauth/callback"
EXPECTED_BODY_FIELDS = ["code", "waba_id", "phone_number_id", "business_id"]


def mask(value: str, head: int = 8, tail: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= head + tail:
        return f"<{len(value)} chars>"
    return f"{value[:head]}...{value[-tail:]}"


def redact(value: str) -> str:
    return value if value else ""


def print_sep(char: str = "=", width: int = 78) -> None:
    print(char * width)


def production_parity_check(production_url: str) -> bool:
    """Verify the deployed backend runs the current callback shape."""
    print_sep()
    print("PRODUCTION PARITY CHECK")
    print_sep()
    url = f"{production_url.rstrip('/')}/openapi.json"
    try:
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        spec = resp.json()
    except Exception as exc:
        print(f"[WARN] Could not fetch production OpenAPI spec from {url}: {exc}")
        return False

    paths = spec.get("paths", {})
    callback = paths.get(EXPECTED_CALLBACK_PATH, {})

    if not callback:
        print(f"[FAIL] Deployed backend has NO {EXPECTED_CALLBACK_PATH} path.")
        return False

    has_post = "post" in callback
    has_get = "get" in callback
    print(f"  POST {EXPECTED_CALLBACK_PATH}: {'present' if has_post else 'MISSING'}")
    print(f"  GET  {EXPECTED_CALLBACK_PATH} (old OAuth redirect flow): {'PRESENT - STALE BUILD' if has_get else 'absent (good)'}")

    body_schema = (
        callback.get("post", {})
        .get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    props = set((body_schema.get("properties") or {}).keys())
    print(f"  Request body fields: {sorted(props)}")

    missing = [f for f in EXPECTED_BODY_FIELDS if f not in props]
    if has_get or not has_post or missing:
        print("[FAIL] Deployed backend does NOT match the current callback shape.")
        print("       The deployment is STALE. Redeploy the current code before testing.")
        return False

    print("[PASS] Deployed backend matches the current callback shape.")
    return True


async def run_exchange(svc: MetaOAuthService, code: str) -> None:
    print_sep()
    print("SINGLE TOKEN EXCHANGE (exactly one attempt)")
    print_sep()
    print(f"  Endpoint: {svc.GRAPH_API_BASE}/oauth/access_token")
    print("  Params: client_id + client_secret + code (NO redirect_uri)")
    print("  redirect_uri: OMITTED (official Embedded Signup FB.login + config_id exchange)")
    print(f"  Code (masked): {mask(code)} (length {len(code)})")
    print_sep()

    success, data, error = await svc.exchange_code_for_token(code)

    if not success:
        print("[RESULT] EXCHANGE FAILED")
        print(f"  Error: {redact(error)}")
        print()
        print("  Meta rejected the code. The exchange request sends")
        print("  client_id + client_secret + code (no redirect_uri) for the")
        print("  Embedded Signup FB.login + config_id flow. Check")
        print("  the checklist from GET /api/integrations/meta/verify and the Meta")
        print("  App Dashboard configuration, then retry with a FRESH code.")
        return

    token = data.get("access_token", "")
    print("[RESULT] EXCHANGE SUCCEEDED")
    print(f"  Access token (masked): {mask(token)}")
    print(f"  Token type: {data.get('token_type', '')}")
    print(f"  Expires in: {data.get('expires_in', '')}")

    # Validate the exchanged token via /debug_token (app_id + granted scopes).
    # The token itself is never printed. This is validation ONLY - the WABA ID
    # and phone number ID are NEVER discovered server-side: they come from the
    # WA_EMBEDDED_SIGNUP session event (the source of truth) and are forwarded
    # by the frontend in the callback payload. /me/businesses is never used.
    print_sep()
    print("TOKEN VALIDATION (debug_token - never used for WABA discovery)")
    print_sep()
    ok, token_info, tok_error = await svc.validate_access_token(token)
    if not ok:
        print(f"[WARN] Token validation failed: {redact(tok_error)}")
        return
    print(f"  App ID: {token_info.get('app_id')}")
    print(f"  Token type: {token_info.get('type')}")
    print(f"  Granted scopes: {token_info.get('scopes') or 'none'}")
    print(f"  Missing WhatsApp scopes: {token_info.get('missing_scopes') or 'none'}")
    print()
    print("  WABA ID / phone number ID are NOT discoverable server-side.")
    print("  They are captured from the WA_EMBEDDED_SIGNUP session event and")
    print("  forwarded by the frontend in POST /api/integrations/meta/oauth/callback.")


async def main(args: argparse.Namespace) -> int:
    if not args.code or len(args.code) < 10:
        print("A fresh exchangeable code is required (--code). Never reuse an old code.")
        return 2

    production_url = args.production_url.rstrip("/")

    if not args.skip_parity_check:
        parity_ok = production_parity_check(production_url)
        if not parity_ok:
            print()
            print("ABORTING exchange probe: production is not running the current code.")
            print("Redeploy first, then re-run with a FRESH code.")
            return 1

    graph_base = f"https://graph.facebook.com/{args.api_version}"
    svc = MetaOAuthService(args.app_id, args.app_secret)
    svc.GRAPH_API_BASE = graph_base

    print_sep()
    print("PROBE CONFIGURATION")
    print_sep()
    print(f"  App ID: {svc.app_id}")
    print(f"  App Secret: <set, never printed>")
    print(f"  Graph API: {graph_base}")

    await run_exchange(svc, args.code)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta Embedded Signup fresh-code exchange probe")
    parser.add_argument("--code", required=True, help="Fresh exchangeable code from a NEW Embedded Signup run")
    parser.add_argument("--production-url", default="https://orym-saas-application.onrender.com")
    parser.add_argument("--skip-parity-check", action="store_true")
    parser.add_argument("--api-version", default="v26.0")
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--app-secret", default=None)
    args = parser.parse_args()

    try:
        from config import get_settings
        settings = get_settings()
        args.app_id = args.app_id or (settings.META_APP_ID or "").strip()
        args.app_secret = args.app_secret or (settings.META_APP_SECRET or "").strip()
    except Exception as exc:
        print(f"[WARN] Could not load settings from .env: {exc}")
        print("       Pass --app-id and --app-secret explicitly to run the probe.")

    if not args.app_id or not args.app_secret:
        print("App ID / App Secret are required (set them in backend/.env or pass --app-id/--app-secret).")
        sys.exit(2)

    sys.exit(asyncio.run(main(args)))
