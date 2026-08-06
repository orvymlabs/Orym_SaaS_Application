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

1. **Missing `redirect_uri` parameter**: When exchanging the authorization code for an access token, Meta's Graph API requires the `redirect_uri` parameter to match the one used in the initial OAuth request.

2. **Insufficient error logging**: The backend wasn't capturing detailed error messages from Meta's API, making it difficult to diagnose the exact issue.

3. **Frontend not passing redirect_uri**: The frontend wasn't explicitly including the `redirect_uri` in the FB.login() call or in the callback to the backend.

## Changes Made

### 1. Backend OAuth Service (`backend/services/meta_oauth.py`)

**Modified `exchange_code_for_token` method:**
- Added `redirect_uri` parameter (optional)
- Enhanced error logging to capture error code, type, and full message from Meta
- Added info logging to track the OAuth flow

**Modified `setup_whatsapp_integration` method:**
- Added `redirect_uri` parameter
- Pass it through to the token exchange
- Added detailed logging for each step

### 2. Backend API Endpoint (`backend/routers/integrations.py`)

**Modified `/api/integrations/meta/oauth/callback` endpoint:**
- Added `redirect_uri` parameter (optional, from request body)
- Enhanced logging to track user_id, code length, and redirect_uri
- Pass redirect_uri to the OAuth service
- Improved error messages

### 3. Frontend (`frontend/app/dashboard/integrations/page.tsx`)

**Modified `launchWhatsAppLogin` function:**
- Calculate the redirect_uri using `appUrl`
- Include `redirect_uri` in the FB.login() options
- Added console logging for debugging

**Modified `handleMetaOAuthCallback` function:**
- Calculate and send `redirect_uri` in the API request to backend
- Added console logging for debugging
- Better error handling

## Technical Details

### OAuth Flow (Fixed)

1. User clicks "Connect WhatsApp Business"
2. Frontend calls `launchWhatsAppLogin()`
3. Frontend calculates: `redirect_uri = https://apps.orvym.com/dashboard/integrations`
4. Frontend launches FB.login() with `redirect_uri` in options
5. Meta OAuth completes, returns authorization code
6. Frontend sends to backend: `{code, redirect_uri}`
7. Backend calls Meta Graph API: `/oauth/access_token` with `{client_id, client_secret, code, redirect_uri}`
8. Meta validates redirect_uri matches and returns access token
9. Backend retrieves WhatsApp Business Account details
10. Backend saves credentials to database
11. Frontend displays success message

### Key Fix Points

**Before:**
```javascript
// Frontend - Missing redirect_uri
window.FB.login(callback, {
  config_id: metaConfig.config_id,
  response_type: 'code',
  override_default_response_type: true
});

// Backend - Not passing redirect_uri
params = {
  "client_id": self.app_id,
  "client_secret": self.app_secret,
  "code": code
}
```

**After:**
```javascript
// Frontend - Includes redirect_uri
const redirect_uri = `${appUrl}/dashboard/integrations`;
window.FB.login(callback, {
  config_id: metaConfig.config_id,
  response_type: 'code',
  override_default_response_type: true,
  redirect_uri: redirect_uri
});

// Backend - Passes redirect_uri
params = {
  "client_id": self.app_id,
  "client_secret": self.app_secret,
  "code": code
}
if redirect_uri:
  params["redirect_uri"] = redirect_uri
```

## Meta App Configuration Required

Ensure the following are configured in Meta Developer Console:

### 1. App Domains
```
apps.orvym.com
```

### 2. Valid OAuth Redirect URIs (Facebook Login → Settings)
```
https://apps.orvym.com/dashboard/integrations
```

### 3. Allowed Domains for JavaScript SDK (Advanced → Security)
```
apps.orvym.com
```

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
   git commit -m "Fix: Add redirect_uri to Meta OAuth flow and enhance error logging"
   git push origin master
   ```
   - Render will auto-deploy from Git

2. **Deploy Frontend to Netlify:**
   ```bash
   git add frontend/app/dashboard/integrations/page.tsx
   git commit -m "Fix: Include redirect_uri in Meta OAuth flow"
   git push origin master
   ```
   - Netlify will auto-deploy from Git

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
