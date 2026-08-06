# CLAUDE.md

## Project Context

This project is a WhatsApp SaaS platform with Meta WhatsApp Business integration.

The application is already connected to a published Meta App and an existing WhatsApp bot is working in production.

DO NOT break, remove, reset, or replace the existing WhatsApp bot configuration.

---

# Current Architecture

## Frontend

- Framework: Next.js
- Production URL: `https://apps.orvym.com`
- Local port: `3000`
- Local URL: `http://localhost:3000`

Important page: `/dashboard/integrations`

Production page: `https://apps.orvym.com/dashboard/integrations`

---

## Backend

- Production: `https://orym-saas-application.onrender.com` (Render)
- Local port: `8001`
- Local URL: `http://localhost:8001`
- Backend webhook URL: `https://orym-saas-application.onrender.com/webhook`

For local development, backend is exposed through ngrok for Meta webhooks.

---

# Meta Embedded Signup Implementation

## Current Implementation (FB.login Popup Flow)

The application uses **Facebook SDK's FB.login()** method with Meta Embedded Signup:

1. User clicks "Connect WhatsApp Business"
2. Frontend calls `FB.login()` with `config_id` and `response_type: 'code'`
3. Meta opens popup/dialog for user to complete signup
4. Popup closes and returns authorization code via **JavaScript callback**
5. Frontend sends **POST** request to backend: `/api/integrations/meta/oauth/callback`
6. Backend exchanges code with Meta Graph API for access token
7. Backend retrieves WhatsApp Business Account details
8. Backend saves credentials to database

**Important:** Meta does NOT redirect to the callback URL in this flow. The callback URL is only used as a reference for Meta's configuration. The code is returned via JavaScript.

---

# Meta OAuth Callback Routes

## POST /api/integrations/meta/oauth/callback

**Purpose:** Handle authorization code from frontend JavaScript (FB.login callback)

**Method:** POST

**Request Body:**
```json
{
  "code": "authorization_code_from_meta",
  "redirect_uri": "https://apps.orvym.com/dashboard/integrations"
}
```

**Response:** Integration details on success

**Used by:** Frontend JavaScript after FB.login() completes

---

## GET /api/integrations/meta/oauth/callback

**Purpose:** Fallback for direct Meta redirects (alternative OAuth flows)

**Method:** GET

**Query Parameters:**
- `code`: Authorization code
- `state`: CSRF protection token
- `error`: Error code if OAuth failed
- `error_description`: Error details

**Response:** HTML page with JavaScript to handle popup or redirect

**Used by:** Meta if configured for traditional redirect-based OAuth

---

# Meta App Configuration

## Production Configuration

**Meta App ID:** `3862862217342382`
**Meta Config ID:** `2432311603846818`

### App Domains
```
apps.orvym.com
orym-saas-application.onrender.com
```

### Valid OAuth Redirect URIs (Facebook Login → Settings)
```
https://apps.orvym.com/dashboard/integrations
```

### Allowed Domains for JavaScript SDK (Advanced → Security)
```
apps.orvym.com
```

### WhatsApp → Configuration → Webhook
```
Callback URL: https://orym-saas-application.onrender.com/webhook
Verify Token: (from database per bot)
```

---

# Environment Variables

## Frontend (Netlify)
```
NEXT_PUBLIC_APP_URL=https://apps.orvym.com
NEXT_PUBLIC_API_URL=https://orym-saas-application.onrender.com
NEXT_PUBLIC_WS_URL=wss://orym-saas-application.onrender.com
NEXT_PUBLIC_WEBHOOK_URL=https://orym-saas-application.onrender.com/webhook
```

## Backend (Render)
```
META_APP_ID=3862862217342382
META_APP_SECRET=4e8c221a2b70d959dfd452ab91a51c06
META_CONFIG_ID=2432311603846818
ALLOWED_ORIGINS=https://apps.orvym.com,https://orym-saas-application.onrender.com
```

---

# Recent Error & Fix

## Error Description
```
Facebook SDK initialized with App ID: 3862862217342382
orym-saas-application.onrender.com/api/integrations/meta/oauth/callback:1  
Failed to load resource: the server responded with a status of 400 ()
```

## Root Cause

The Meta OAuth token exchange was failing because:

1. **Missing `redirect_uri` parameter:** Meta's Graph API token exchange requires the `redirect_uri` parameter to match the one used in the authorization request
2. **Insufficient error logging:** Backend wasn't capturing detailed Meta API error messages
3. **Frontend not passing redirect_uri:** The frontend wasn't including `redirect_uri` in the FB.login() options or backend request

## Changes Made

### 1. Backend OAuth Service (`backend/services/meta_oauth.py`)
- Added `redirect_uri` parameter to `exchange_code_for_token()`
- Enhanced error logging to capture Meta API error codes and messages
- Added step-by-step logging for debugging

### 2. Backend API Routes (`backend/routers/integrations.py`)
- Added GET endpoint for direct Meta redirects (fallback)
- Updated POST endpoint to accept and use `redirect_uri`
- Enhanced logging throughout OAuth flow

### 3. Frontend (`frontend/app/dashboard/integrations/page.tsx`)
- Added `redirect_uri` to FB.login() options
- Send `redirect_uri` in POST request to backend
- Added console logging for debugging

---

# Testing OAuth Flow

## Expected Success Flow

1. ✅ User clicks "Connect WhatsApp Business"
2. ✅ Console log: "Launching WhatsApp login with redirect_uri: https://apps.orvym.com/dashboard/integrations"
3. ✅ Meta popup opens
4. ✅ User completes signup
5. ✅ Console log: "OAuth code received, length: [number]"
6. ✅ Console log: "Sending OAuth callback with code and redirect_uri: ..."
7. ✅ Backend log: "POST OAuth callback received for user X"
8. ✅ Backend log: "Token exchange successful"
9. ✅ Backend log: "Successfully connected WhatsApp for user X"
10. ✅ Frontend: "WhatsApp connected successfully!"

## Debugging Failed OAuth

If OAuth fails:

1. **Check browser console** for error messages
2. **Check Render backend logs** for detailed Meta API errors
3. **Verify redirect_uri** matches Meta App settings exactly
4. **Confirm Meta App is Live** (not Development mode)
5. **Check WhatsApp API permissions** in Meta App

---

# Local Development

For local testing with HTTPS (required by Meta):

1. Start frontend: `npm run dev` (port 3000)
2. Start backend: `uvicorn main:app --reload --port 8001`
3. Expose frontend with ngrok: `ngrok http 3000`
4. Expose backend with ngrok: `ngrok http 8001`
5. Update `.env.local`:
   ```
   NEXT_PUBLIC_APP_URL=https://[frontend-ngrok-url]
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```
6. Add ngrok URLs to Meta App settings:
   - App Domains: `[frontend-ngrok-domain]`
   - Valid OAuth Redirect URIs: `https://[frontend-ngrok-domain]/dashboard/integrations`
   - Allowed Domains for JavaScript SDK: `[frontend-ngrok-domain]`

---

# Critical Rules

## 1. Do not break the existing WhatsApp bot

The existing bot is working in production.

DO NOT:
- Create a new Meta App
- Delete or unpublish the Meta App
- Remove the WhatsApp phone number
- Reset WhatsApp configuration
- Change working production credentials
- Disconnect the WhatsApp Business Account

## 2. Do not hardcode temporary URLs

Use environment variables for all URLs.

## 3. Never commit secrets

Keep credentials in environment variables only.

---

# Success Criteria

- ✅ Production OAuth flow works without errors
- ✅ Users can connect WhatsApp via Embedded Signup
- ✅ Backend logs show successful token exchange
- ✅ WhatsApp credentials saved to database
- ✅ Existing WhatsApp bot continues working
- ✅ No 400 errors in browser console
- ✅ Detailed error logging for troubleshooting

---

# Files Modified (Recent Fix)

- `backend/services/meta_oauth.py` - OAuth service with redirect_uri support
- `backend/routers/integrations.py` - GET and POST callback endpoints
- `frontend/app/dashboard/integrations/page.tsx` - Frontend OAuth flow
- `ERROR_FIX_DOCUMENTATION.md` - Detailed error analysis

---

# Next Steps

1. Deploy changes to production (Render + Netlify auto-deploy on git push)
2. Verify Meta App settings match production URLs
3. Test OAuth flow in production
4. Monitor Render logs for any errors
5. Verify existing bot still works after deployment
