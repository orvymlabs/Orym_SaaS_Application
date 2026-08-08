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

---

# Second Fix: (#100) Tried accessing nonexisting field (phone_numbers)

After the `redirect_uri` issue was resolved, the next production failure was:

```
HTTP 400
(#100) Tried accessing nonexisting field (phone_numbers)
```

## Root cause

`setup_whatsapp_integration()` identified the WABA ID with:

```
GET /me?fields=id,name
```

and then treated that `id` as the WABA ID:

```
GET /<id>/phone_numbers
```

But `GET /me` returns the **token owner** (the business / system user), **not** the
WhatsApp Business Account (WABA). `phone_numbers` is an **edge/connection of the
WhatsAppBusinessAccount node** — it is NOT a field on a Business object. Querying
`/<business_id>/phone_numbers` therefore returns:

```
(#100) Tried accessing nonexisting field (phone_numbers)
```

## Correct approach (per Meta docs)

Meta's WhatsApp Embedded Signup docs ("Manage accounts > Get shared WABA ID with
access token") specify the Debug Token endpoint to identify the WABA from the token:

```
GET /debug_token?input_token=<SIGNUP_TOKEN>&access_token=<APP_ACCESS_TOKEN>
```

The response's `data.granular_scopes` entry for `whatsapp_business_management` lists
the WABA IDs granted to the token (most recently onboarded first). Then query the
WABA's phone_numbers **edge**:

```
GET /<WABA_ID>/phone_numbers?access_token=<BUSINESS_TOKEN>
```

## What changed (`backend/services/meta_oauth.py`)

1. **New `get_waba_ids_from_token(access_token)`** — calls `GET /debug_token`
   (authorized with the app access token `<APP_ID>|<APP_SECRET>`), extracts WABA IDs
   from `granular_scopes[whatsapp_business_management/messaging].target_ids` and the
   business/system-user ID from `data.user_id`.
2. **New `get_waba_details(waba_id, access_token)`** — `GET /<WABA_ID>?fields=id,name`
   to read the WABA node's `name` (non-fatal if it fails).
3. **`get_phone_numbers()` unchanged URL** — it already called `/<waba_id>/phone_numbers`
   (the correct edge); it was failing only because `waba_id` was wrong. Added safe
   request logging.
4. **`setup_whatsapp_integration()`** — now orchestrates:
   exchange code → debug_token (WABA ID + business ID) → WABA details → phone_numbers edge.
   `business_id` (from `debug_token.user_id`) and `waba_id` are now correctly distinct.
5. **Safe request logging** — every Graph API call logs endpoint, HTTP method, API
   version, object ID/edge and `fields`; tokens/secrets/codes are always redacted.

`/me` is no longer used anywhere in the onboarding flow.

## Flow now

```
Embedded Signup
→ exchange code (redirect_uri EXACT)
→ access token
→ GET /debug_token  → WABA ID (granular_scopes target_ids) + business/system user ID
→ GET /<WABA_ID>?fields=id,name
→ GET /<WABA_ID>/phone_numbers   (EDGE, correct object)
→ phone number ID + display phone number
→ save WhatsApp connection
```

## Tests

- `backend/test_meta_oauth_mock.py` — `test_setup_whatsapp_integration_full_flow`
  (exchange → debug_token → WABA details → phone_numbers) and
  `test_phone_numbers_edge_regression` (asserts no `fields=phone_numbers` anywhere and
  `phone_numbers` is only called against the real WABA ID).
- All OAuth tests pass: `test_oauth_params.py`, `test_exchange_params.py`,
  `test_meta_oauth_mock.py`, `test_meta_callback_e2e.py`.
