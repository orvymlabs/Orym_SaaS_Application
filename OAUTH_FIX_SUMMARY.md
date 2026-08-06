# Meta OAuth Fix - Implementation Summary (CORRECTED)

> ⚠️ This supersedes the earlier versions of this document. The previous fix
> (sending `redirect_uri` in the token exchange) did NOT work in production.
> Meta rejects it with:
> `400 Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request`

## Root Cause Analysis

### The actual Meta Embedded Signup behavior

Meta WhatsApp **Embedded Signup** is launched via `FB.login()` with `config_id`:

```js
FB.login(fbLoginCallback, {
  config_id: "2432311603846818",
  response_type: "code",
  override_default_response_type: true,
  extras: { setup: {} },
});
```

The exchangeable code is returned to the page **via the JavaScript callback**, not via a URL
redirect. So:

1. **Authorization has NO redirect_uri** — the JS SDK does not use one for Embedded Signup.
2. **Token exchange must ALSO have NO redirect_uri** — Meta's Embedded Signup docs
   ("Onboarding business customers as a Tech Provider") exchange the code with
   `GET /oauth/access_token?client_id&client_secret&code` only.

### What was broken (WRONG)

The previous code sent a `redirect_uri` (the current page URL) to the backend, and the
backend forwarded it to Meta:

```
Frontend -> Backend : POST /api/integrations/meta/oauth/callback  {"code", "redirect_uri": "https://apps.orvym.com/dashboard/integrations"}
Backend  -> Meta     : GET https://graph.facebook.com/v21.0/oauth/access_token?client_id=...&client_secret=...&code=...&redirect_uri=https://apps.orvym.com/dashboard/integrations
```

Meta rejected it because the authorization dialog never used that redirect_uri.

A separate blocker: the OAuth dialog showed
`Can't load URL: The domain of this URL isn't included in the app's domains.` because the
real page domain `apps.orvym.com` was not registered in the Meta app.

## Solution Implemented

### 1. Frontend (`frontend/app/dashboard/integrations/page.tsx`)

- `FB.login()` keeps `config_id`, `response_type: 'code'`, `override_default_response_type: true`,
  `extras.setup = {}` — **no redirect_uri** (matches Meta's official sample).
- `handleMetaOAuthCallback()` now sends **only the code** to the backend:
  ```typescript
  const result = await apiPost("/api/integrations/meta/oauth/callback", {
    code
  });
  ```
- Logs `redirect_uri: NOT INCLUDED (correct for Embedded Signup)`.

### 2. Backend endpoint (`backend/routers/integrations.py`)

- `redirect_uri` in `POST /api/integrations/meta/oauth/callback` is now **optional**
  (`Body(None, embed=True)`) for backward compatibility and is logged but NOT forwarded.
- Frontend request body is now: `{ "code": "..." }`.

### 3. Backend OAuth service (`backend/services/meta_oauth.py`)

- `exchange_code_for_token()` sends **only** `client_id`, `client_secret`, `code` to
  `https://graph.facebook.com/v26.0/oauth/access_token`.
- `redirect_uri` is only added if an explicit non-empty value is supplied (non-Embedded flows).
- Graph API base bumped to `v26.0` (matches the SDK version used by the frontend).

### 4. Meta App Dashboard configuration

See `PRODUCTION_META_CONFIG.md`. The real domain `apps.orvym.com` must be in:

- **App Domains** (Settings > Basic)
- **Valid OAuth Redirect URIs** (Facebook Login > Settings):
  `https://apps.orvym.com/` and `https://apps.orvym.com/dashboard/integrations`
- **Allowed Domains for the JavaScript SDK** (Facebook Login > Settings)
- **Facebook Login for Business > Settings** (same entries)

## The correct OAuth flow

```
┌─────────────┐
│  Frontend   │  1. FB.login({config_id, response_type:'code', ...})
│  (Browser)  │     NO redirect_uri
└──────┬──────┘
       ▼
┌─────────────┐  2. User authorizes in popup
│ Meta Popup  │
└──────┬──────┘
       │  3. Exchangeable code returned via JS callback
       ▼
┌─────────────┐  4. POST /api/integrations/meta/oauth/callback
│  Frontend   │     Body: {"code": "..."}   ← NO redirect_uri
└──────┬──────┘
       ▼
┌─────────────┐  5. GET https://graph.facebook.com/v26.0/oauth/access_token
│   Backend   │     Params: {client_id, client_secret, code}   ← NO redirect_uri
└──────┬──────┘
       │  6. Meta returns business token
       ▼
┌─────────────┐
│    Meta     │
└─────────────┘
```

## Files Modified

1. `frontend/app/dashboard/integrations/page.tsx` — removed `redirect_uri` from callback body
2. `backend/routers/integrations.py` — `redirect_uri` optional, updated logging
3. `backend/services/meta_oauth.py` — token exchange omits `redirect_uri`, Graph API v26.0
4. `PRODUCTION_META_CONFIG.md` — required Meta App settings with the ACTUAL domain

## Status

✅ The Embedded Signup code exchange now omits `redirect_uri`, matching Meta's
Embedded Signup documentation. The `apps.orvym.com` domain must be registered in the
Meta App (App Domains + Valid OAuth Redirect URIs + Allowed Domains for the JS SDK).
