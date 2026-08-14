# Meta OAuth Fix - Implementation Summary (FINAL)

> ⚠️ This supersedes all earlier versions of this document, including the
> previous "manual dialog URL + redirect_uri" theory below this notice. That
> theory was also wrong. The actual root cause was never `redirect_uri` -
> see "Root Cause Analysis" below.

## Root Cause Analysis

### The actual bug

The frontend's `FB.login()` call (in `frontend/app/dashboard/integrations/page.tsx`)
was missing one field in its `extras` option:

```js
extras: {
  setup: {},
  featureType: 'whatsapp_business_app_onboarding', // was missing entirely
  sessionInfoVersion: '3', // was the number 3, not the string '3'
}
```

Without `featureType`, Meta's server never recognized the popup session as a
WhatsApp-specific Embedded Signup flow. The popup still completed normally,
the returned code still looked correctly formatted (~450 chars), and the
`WA_EMBEDDED_SIGNUP` session message still arrived with correct WABA data -
but the code itself was invalid for exchange. Every attempt to exchange it
failed with:

```
400 Error validating verification code. Please make sure your redirect_uri
is identical to the one you used in the OAuth dialog request
(code 100 / subcode 36008)
```

### Why `redirect_uri` was a red herring

That error message names `redirect_uri`, so it's the natural first suspect -
but it's Meta's generic catch-all for "this code is not valid," not a real
diagnosis. Five different `redirect_uri` values were tried against the live
API with fresh, single-use codes, and **all five failed identically**:

1. `redirect_uri=""` (empty string) - the original production failure
2. `redirect_uri` omitted entirely
3. `redirect_uri` = the exact frontend page URL
4. `redirect_uri` = the exact dynamic `xd_arbiter` channel URL, captured
   byte-for-byte from Meta's own generated OAuth dialog request
5. A manually-built redirect-based OAuth dialog flow (the earlier version of
   this document) instead of the `FB.login()` popup

None of it mattered, because the code being generated was invalid before any
of these requests were even sent. This was only found by comparing our
`FB.login()` call, field by field, against Chatwoot's real, production
open-source implementation
(`app/javascript/dashboard/routes/dashboard/settings/inbox/channels/whatsapp/utils.js`
in `chatwoot/chatwoot` on GitHub) - their `extras` object had `featureType`,
ours didn't.

## Solution Implemented

### 1. Frontend (`frontend/app/dashboard/integrations/page.tsx`)

Standard `FB.login()` popup flow (not a manual redirect-based dialog):

```js
window.FB.login(callback, {
  config_id: metaConfig.config_id,
  response_type: 'code',
  override_default_response_type: true,
  extras: {
    setup: {},
    featureType: 'whatsapp_business_app_onboarding',
    sessionInfoVersion: '3',
  },
});
```

`redirect_uri` is **not** sent in the callback payload to the backend - it
isn't needed.

### 2. Backend endpoint (`backend/routers/integrations.py`)

`POST /api/integrations/meta/oauth/callback` accepts an optional
`redirect_uri` field for forward compatibility, but the frontend doesn't
send one and the exchange doesn't require it.

### 3. Backend OAuth service (`backend/services/meta_oauth.py`)

`exchange_code_for_token()` sends only:

```
GET https://graph.facebook.com/v26.0/oauth/access_token
  ?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>
```

matching Chatwoot's proven-working implementation
(`app/services/whatsapp/facebook_api_client.rb`).

## Access token type: System-user, not User

The Meta Configuration (`META_CONFIG_ID`) can be created with either **User
access token** or **System-user access token** - this choice can't be
changed after the configuration is created. We're using **System-user**
(current `META_CONFIG_ID=1015491284652424`).

This wasn't the fix for the 36008 bug above - that was purely the
`featureType` field, and it's plausible the original User-access-token
config would have also worked once `featureType` was added. We didn't
re-test that combination once the real fix was found.

System-user is still the right choice for this product regardless:

- **User access token**: tied to the person who logged in, expires in
  hours. Fine for a one-off test, wrong for production - Orvym needs to
  keep sending messages and managing the WABA long after the customer's
  one-time signup click, without them being present or re-authenticating.
- **System-user access token**: long-lived, not tied to any one person's
  session - the standard choice for a Tech Provider (Orvym) needing
  continuing, automated access to a client's WhatsApp Business Account.

**Production note:** `META_CONFIG_ID` is set locally in `backend/.env`
(gitignored, not deployed automatically). Render's environment variables
must be updated to `1015491284652424` separately before deploying, or
production will keep using the old config.

## Required Meta App Dashboard settings

See `PRODUCTION_META_CONFIG.md`. Summary:

- **Allowed Domains for the JavaScript SDK**: `apps.orvym.com`
- **Valid OAuth Redirect URIs**: `https://apps.orvym.com/dashboard/integrations/`
  (kept registered for Strict Mode / dashboard requirements even though the
  exchange doesn't send this value)
- **Facebook Login for Business > Settings**: Client OAuth Login / Web OAuth
  Login / Login with the JavaScript SDK / Embedded Browser OAuth Login / Use
  Strict Mode for redirect URIs - all enabled
- Configuration `1015491284652424`: System-user access token, permissions
  `business_management`, `whatsapp_business_management`,
  `whatsapp_business_messaging`

## Files Modified

1. `frontend/app/dashboard/integrations/page.tsx` - `FB.login()` extras now
   include `featureType`; `sessionInfoVersion` sent as a string; no
   `redirect_uri` sent to the backend
2. `backend/routers/integrations.py` - callback accepts optional
   `redirect_uri` (not required)
3. `backend/schemas/integration.py` - optional `redirect_uri` field
4. `backend/services/meta_oauth.py` - exchange sends only
   `client_id`/`client_secret`/`code`
5. `backend/main.py` - CORS `allow_headers` includes
   `ngrok-skip-browser-warning` (local testing only, harmless in production)
6. `backend/.env` - `META_CONFIG_ID` updated to the System-user config
   (needs the same update in Render's dashboard before deploying)

## Status

✅ Confirmed working end-to-end in local testing: token exchange, token
validation, WABA validation, phone number verification, and webhook
subscription all succeeded, ending in `POST /api/integrations/meta/oauth/callback → 200 OK`.
Not yet deployed to production - see "Files Modified" and the `META_CONFIG_ID`
note above before deploying.

---

# WABA ID resolution (`#100 Tried accessing nonexisting field (phone_numbers)`)

This section is unrelated to the redirect_uri/featureType issue above and
remains accurate.

## Root cause

An earlier version of `setup_whatsapp_integration()` identified the WABA ID
with `GET /me?fields=id,name` and treated that `id` as the WABA ID, then
queried `GET /<id>/phone_numbers`. But `GET /me` returns the **token
owner** (the business/system user), **not** the WhatsApp Business Account.
`phone_numbers` is an edge on the `WhatsAppBusinessAccount` node, not a
field on a Business object, so this produced:

```
(#100) Tried accessing nonexisting field (phone_numbers)
```

## Correct approach (per Meta docs)

Meta's WhatsApp Embedded Signup docs specify using `/debug_token` to
identify the WABA from the access token:

```
GET /debug_token?input_token=<TOKEN>&access_token=<APP_ID>|<APP_SECRET>
```

`data.granular_scopes` for the `whatsapp_business_management` scope lists
the WABA IDs granted to the token (most recently onboarded first). Then
query the WABA's `phone_numbers` edge directly:

```
GET /<WABA_ID>/phone_numbers?access_token=<BUSINESS_TOKEN>
```

## Current flow (`backend/services/meta_oauth.py`)

```
exchange code
→ access token
→ GET /debug_token → WABA ID (granular_scopes target_ids) + business/system user ID
→ GET /<WABA_ID>?fields=id,name
→ GET /<WABA_ID>/phone_numbers   (edge, correct object)
→ phone number ID + display phone number
→ save WhatsApp connection
```

`/me` is not used anywhere in the onboarding flow.
