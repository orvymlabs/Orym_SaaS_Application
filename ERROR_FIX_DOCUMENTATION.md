# Meta WhatsApp OAuth Error Fix

## Error Description

**Production Error:**
```
Facebook SDK initialized with App ID: 3862862217342382
orym-saas-application.onrender.com/api/integrations/meta/oauth/callback:1  
Failed to load resource: the server responded with a status of 400 ()
```

**Issue Location:** Production environment at `https://apps.orvym.com/dashboard/integrations`

## Root Cause

The Meta OAuth token exchange was failing with a 400 Bad Request error because:

1. **A `redirect_uri` was being sent during the token exchange.** Meta WhatsApp
   **Embedded Signup** (FB.login + config_id) returns the exchangeable code via the
   JavaScript callback and does NOT use a redirect_uri during authorization. Passing
   ANY redirect_uri in `GET /oauth/access_token` triggers:
   `Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request`

2. **The page domain was not registered in the Meta App.** The frontend runs at
   `https://apps.orvym.com/dashboard/integrations`. The OAuth dialog refused to load with:
   `Can't load URL: The domain of this URL isn't included in the app's domains.` because
   `apps.orvym.com` was missing from App Domains / Valid OAuth Redirect URIs /
   Allowed Domains for the JavaScript SDK.

## Changes Made

### 1. Backend OAuth Service (`backend/services/meta_oauth.py`)

**Modified `exchange_code_for_token` method:**
- Sends ONLY `client_id`, `client_secret`, `code` to
  `https://graph.facebook.com/v26.0/oauth/access_token` (no `redirect_uri`).
- `redirect_uri` accepted only for backward compatibility; not forwarded for Embedded Signup.
- Enhanced error logging to capture error code, type, and full message from Meta
- Graph API version bumped to `v26.0`

**Modified `setup_whatsapp_integration` method:**
- `redirect_uri` is now optional and documented as ignored for Embedded Signup

### 2. Backend API Endpoint (`backend/routers/integrations.py`)

**Modified `/api/integrations/meta/oauth/callback` endpoint:**
- `redirect_uri` is now **optional** (`Body(None, embed=True)`)
- Frontend body is now `{ "code": "..." }` — no redirect_uri
- Enhanced logging to track user_id, code length, and whether redirect_uri was provided

### 3. Frontend (`frontend/app/dashboard/integrations/page.tsx`)

**Modified `handleMetaOAuthCallback` function:**
- Sends ONLY `{ code }` to the backend callback
- Removed the `redirect_uri` computation entirely
- Added console logging stating `redirect_uri: NOT INCLUDED (correct for Embedded Signup)`

**Modified `launchWhatsAppLogin` function:**
- `FB.login()` uses `config_id`, `response_type: 'code'`, `override_default_response_type: true`,
  `extras: { setup: {} }` — NO redirect_uri (matches Meta's official Embedded Signup sample)

## Technical Details

### OAuth Flow (Fixed)

1. User clicks "Connect WhatsApp Business"
2. Frontend calls `launchWhatsAppLogin()`
3. Frontend launches FB.login() with `config_id` (no redirect_uri)
4. Meta Embedded Signup completes, returns exchangeable code via JS callback
5. Frontend sends to backend: `{code}`
6. Backend calls Meta Graph API: `GET /oauth/access_token` with `{client_id, client_secret, code}` (no redirect_uri)
7. Meta returns access token
8. Backend retrieves WhatsApp Business Account details
9. Backend saves credentials to database
10. Frontend displays success message

### Key Fix Points

**Before (BROKEN):**
```javascript
// Frontend - sent redirect_uri
const result = await apiPost("/api/integrations/meta/oauth/callback", {
  code,
  redirect_uri: currentPageUrl
});

// Backend - forwarded redirect_uri to Meta
params = {
  "client_id": self.app_id,
  "client_secret": self.app_secret,
  "code": code,
  "redirect_uri": redirect_uri   // ❌ causes the 400
}
```

**After (CORRECT):**
```javascript
// Frontend - only the code
const result = await apiPost("/api/integrations/meta/oauth/callback", {
  code
});

// Backend - Embedded Signup exchange has no redirect_uri
params = {
  "client_id": self.app_id,
  "client_secret": self.app_secret,
  "code": code
}
```

## Meta App Configuration Required

Ensure the following are configured in Meta Developer Console (see `PRODUCTION_META_CONFIG.md`):

### 1. App Domains (Settings > Basic)
```
apps.orvym.com
```

### 2. Valid OAuth Redirect URIs (Facebook Login → Settings)
```
https://apps.orvym.com/
https://apps.orvym.com/dashboard/integrations
```

### 3. Allowed Domains for JavaScript SDK (Facebook Login → Settings)
```
apps.orvym.com
```

### 4. Facebook Login for Business → Settings
Same entries as #2 and #3.

> Only the ACTUAL domain serving the frontend (`apps.orvym.com`) should be added.
> Do not add random domains.

## Environment Variables

### Frontend (Netlify)
```
NEXT_PUBLIC_APP_URL=https://apps.orvym.com
```

### Backend (Render)
```
META_APP_ID=3862862217342382
META_APP_SECRET=4e8c221a2b70d959dfd452ab91a51c06
META_CONFIG_ID=2432311603846818
```

## Deployment Steps

1. **Deploy Backend to Render:**
   ```bash
   git add backend/services/meta_oauth.py backend/routers/integrations.py
   git commit -m "Fix: omit redirect_uri from Embedded Signup token exchange"
   git push origin master
   ```
   - Render will auto-deploy from Git

2. **Build & Deploy Frontend to Hostinger:**
   ```bash
   cd frontend
   npm run build
   ```
   - Upload the generated `out/` directory to Hostinger (apps.orvym.com)

3. **Verify Meta App Settings:**
   - Visit https://developers.facebook.com/apps/3862862217342382
   - Confirm all redirect URIs are whitelisted
   - Check that App ID and Config ID match environment variables

4. **Test in Production:**
   - Visit https://apps.orvym.com/dashboard/integrations
   - Click "Connect WhatsApp Business"
   - Complete the OAuth flow
   - Check browser console and backend logs for any errors

## Expected Success Indicators

✅ No 400 errors in browser console
✅ Backend logs show: "Token exchange successful"
✅ Backend logs show: "Successfully connected WhatsApp for user X"
✅ Frontend displays: "WhatsApp connected successfully!"
✅ WhatsApp phone number appears in the integration card

## Debugging

If the error persists after deployment:

1. **Check browser console** for detailed error messages
2. **Check backend logs on Render** for the detailed Meta API error
3. **Verify redirect_uri** in logs matches Meta App settings exactly
4. **Confirm Meta App is in Live mode** (not Development mode)
5. **Check Meta App permissions** for WhatsApp Business API access

## Related Files Modified

- `backend/services/meta_oauth.py` - OAuth service with redirect_uri support
- `backend/routers/integrations.py` - API endpoint accepting redirect_uri
- `frontend/app/dashboard/integrations/page.tsx` - Frontend OAuth flow

## References

- [Meta OAuth Documentation](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow)
- [WhatsApp Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup)
