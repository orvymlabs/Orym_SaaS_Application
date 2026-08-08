# Meta OAuth Fix - Implementation Summary (CORRECTED)

> ⚠️ This supersedes all earlier versions of this document.
> The previous "solutions" (sending a page-URL `redirect_uri`, then
> `redirect_uri=""` empty string) both failed in production with:
> `400 Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request`

## Root Cause Analysis

### Why the earlier approaches failed

WhatsApp **Embedded Signup** launched via the JS SDK `FB.login({config_id, ...})`
returns the exchangeable code through an internal callback. The JS SDK opens the
OAuth dialog with an **internal `redirect_uri`** (`https://staticxx.facebook.com/x/connect/xd_arbiter/...`)
that we do not control. Meta binds the code to that internal URI, so:

- Sending the page URL (`https://apps.orvym.com/dashboard/integrations`) → **mismatch** (dialog never used it).
- Sending `redirect_uri=""` → **mismatch** (empty string is not identical to the recorded URI).
- Omitting `redirect_uri` → also rejected by Meta's OAuth server for this app/config.

### The fix: control `redirect_uri` by building the dialog URL manually

Meta's **"Manually Build a Login Flow"** documentation says the token exchange
`redirect_uri` is required and **must be the same as the one used in the OAuth dialog
request**. And the Facebook Login for Business documentation says that when building
the login flow manually you include your **`config_id`** as an optional parameter.

So the frontend now builds the dialog URL itself and therefore **owns** the
`redirect_uri`. Because we set it, we can guarantee the exchange uses the byte-for-byte
identical value.

## Solution Implemented

### 1. Frontend (`frontend/app/dashboard/integrations/page.tsx`)

- Replaced `FB.login(...)` with a manually built dialog URL:

  ```
  https://www.facebook.com/v26.0/dialog/oauth
    ?client_id=<APP_ID>
    &redirect_uri=<window.location.origin + window.location.pathname>
    &response_type=code
    &config_id=<CONFIG_ID>
    &override_default_response_type=true
    &state=<csrf-state>
  ```

- A `useEffect` detects the `?code=...&state=...` redirect-back, verifies the CSRF
  state against `sessionStorage`, cleans the URL, and calls the backend with the
  **exact** `redirect_uri`:

  ```typescript
  const result = await apiPost("/api/integrations/meta/oauth/callback", {
    code,
    redirect_uri: oauthRedirectUri,
  });
  ```

- Removed the misleading log `"backend uses empty-string redirect_uri ..."`.

### 2. Backend endpoint (`backend/routers/integrations.py`)

- `POST /api/integrations/meta/oauth/callback` accepts `{ code, redirect_uri }`.
  `redirect_uri` is optional; when present it is forwarded verbatim to the exchange.
- Logs: user_id, code length, redirect_uri, flow type. Never logs the secret/token/code.

### 3. Backend OAuth service (`backend/services/meta_oauth.py`)

- `exchange_code_for_token()` sends:
  ```
  GET https://graph.facebook.com/v26.0/oauth/access_token
    client_id, client_secret, code
    (+ redirect_uri ONLY when an explicit non-empty value is supplied)
  ```
- **Empty-string `redirect_uri` is removed entirely** — never constructed, never sent.
- Single deterministic attempt (no guessing variants). Graph API `v26.0`.

## The correct OAuth flow

```
┌─────────────┐  1. Build dialog URL with OUR redirect_uri + config_id + state
│  Frontend   │  2. window.location.href -> facebook.com/v26.0/dialog/oauth
│  (Browser)  └──────────────────────────────►
└─────────────┘
        ▲                                        │ 3. User completes WhatsApp Embedded Signup
        │  5. Redirect back to                     ▼
        │     redirect_uri?code=...&state=... ┌─────────────┐
        │                                       │ Meta Popup │
        │ 6. POST {code, redirect_uri}          └─────────────┘
        │
        ▼
┌─────────────┐  7. GET graph.facebook.com/v26.0/oauth/access_token
│   Backend   │     client_id + client_secret + code + redirect_uri (EXACT)
└──────┬──────┘
       │  8. Meta returns business token
       ▼
┌─────────────┐
│    Meta     │
└─────────────┘
```

## Required Meta App Dashboard settings

See `PRODUCTION_META_CONFIG.md`. The page URL where the flow runs must be registered:

- **App Domains**: `apps.orvym.com`
- **Valid OAuth Redirect URIs**:
  - `https://apps.orvym.com/`
  - `https://apps.orvym.com/dashboard/integrations`
  - `https://apps.orvym.com/dashboard/integrations/` (trailing-slash variant)
- **Allowed Domains for the JavaScript SDK**: `apps.orvym.com`
- **Facebook Login for Business > Settings**: same entries as above, with
  Client OAuth Login / Web OAuth Login / Enforce HTTPS enabled.

## Files Modified

1. `frontend/app/dashboard/integrations/page.tsx` — manual dialog flow + redirect-back handler
2. `backend/routers/integrations.py` — callback accepts/forwards `redirect_uri`, corrected logging
3. `backend/services/meta_oauth.py` — exchange omits `redirect_uri` unless exact value supplied; empty string banned
4. `backend/test_oauth_params.py` — updated to reflect corrected behavior
5. `backend/test_exchange_params.py` — new verification test
6. `PRODUCTION_META_CONFIG.md` — corrected operational config

## Status

✅ The code exchange is deterministic: it sends the **exact** dialog `redirect_uri` when
one is provided and never sends an empty string. The production bundle has been rebuilt
and verified (the "empty-string" message is gone; the manual dialog flow is present).
