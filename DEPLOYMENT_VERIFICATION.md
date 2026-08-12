# WhatsApp Embedded Signup - Deployment Verification Guide

## Status: ✅ CODE READY FOR PRODUCTION

All code changes to fix Meta error_subcode 36008 are complete and tested.

---

## What Was Fixed

### The Problem
Production was failing with Meta error 100 / subcode 36008:
```
OAUTH_REDIRECT_URI_MISMATCH: OAuth authorization code is invalid or was issued for a different redirect URI.
```

### The Root Cause
The WhatsApp Embedded Signup uses `FB.login()` with `config_id`, which binds the authorization code to **Meta's INTERNAL redirect URI**. The backend was sending the canonical `redirect_uri` in the token exchange, which didn't match Meta's internal value, causing error 36008.

### The Solution
The token exchange now sends **ONLY** `client_id`, `client_secret`, and `code` - NO `redirect_uri` parameter at all.

---

## Code Changes Summary

### ✅ Backend Changes
**File**: `backend/services/meta_oauth.py`
- **Line 242-246**: `exchange_code_for_token()` - Parameters dictionary contains ONLY:
  ```python
  params = {
      "client_id": self.app_id,
      "client_secret": self.app_secret,
      "code": code,
  }
  # NO redirect_uri - intentionally excluded
  ```
- **Line 161**: Production log confirms `redirect_uri included: False`

**File**: `backend/schemas/integration.py`
- **Line 5-28**: `MetaOAuthCallbackRequest` - Schema excludes `redirect_uri` field
- Contains only: `code`, `waba_id`, `phone_number_id`, `business_id`

**File**: `backend/routers/integrations.py`
- **Line 657-850**: `/api/integrations/meta/oauth/callback` endpoint
- Does NOT forward any `redirect_uri` to the OAuth service

### ✅ Frontend Changes
**File**: `frontend/app/dashboard/integrations/page.tsx`
- **Line 718-723**: Callback payload excludes `redirect_uri`:
  ```javascript
  await apiPost("/api/integrations/meta/oauth/callback", {
    code,
    waba_id: wabaId || null,
    phone_number_id: phoneNumberId || null,
    business_id: businessId || null,
  });
  // NO redirect_uri in payload
  ```

### ✅ Tests
All tests pass:
- `test_exchange_params.py` - ✅ PASS
- `test_production_ready.py` - ✅ PASS (all 4 tests)

---

## Deployment Checklist

### 1. ✅ Backend Code Verification (COMPLETED)
- [x] Token exchange sends NO `redirect_uri`
- [x] Schema excludes `redirect_uri`
- [x] Router endpoint correct
- [x] All tests pass

### 2. ✅ Frontend Code Verification (COMPLETED)
- [x] Callback payload excludes `redirect_uri`
- [x] Embedded Signup flow implementation correct
- [x] Message listener registered correctly

### 3. ⚠️ Backend Deployment to Render (ACTION REQUIRED)

#### Current Deployment Target
- **Service**: `orym-saas-application.onrender.com`
- **Platform**: Render
- **Branch**: `master`

#### Deployment Steps

**Option A: Automatic Deployment (if connected to GitHub)**
1. Push changes to `master` branch
2. Render automatically deploys from GitHub
3. Wait for deployment to complete
4. Verify deployment logs

**Option B: Manual Deployment via Render Dashboard**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Find service: `orym-saas-application`
3. Click "Manual Deploy" → "Deploy latest commit"
4. Monitor deployment logs
5. Wait for "Live" status

#### Verify Backend Deployment
```bash
# Check if the fix is deployed
curl -s https://orym-saas-application.onrender.com/health
# or
curl -s https://orym-saas-application.onrender.com/api/integrations/meta/config
```

Expected response should include current Meta config.

### 4. ⚠️ Frontend Deployment (ACTION REQUIRED)

#### Current Deployment Target
- **URL**: `https://apps.orvym.com`
- **Platform**: Hostinger (FTP)
- **Deployment**: GitHub Actions (automatic on push to `master`)

#### Deployment Steps
Frontend deploys automatically via GitHub Actions when pushing to `master`:
1. Push to `master` branch
2. GitHub Actions workflow triggers
3. Build completes
4. FTP deployment to Hostinger
5. Changes live at `https://apps.orvym.com`

#### Verify Frontend Deployment
1. Open `https://apps.orvym.com/dashboard/integrations`
2. Check browser console for frontend version/logs
3. Inspect Network tab when clicking "Connect WhatsApp Business"

---

## Post-Deployment Verification

### Step 1: Check Production Logs

After deploying to Render, the backend will log the exact parameters sent to Meta:

```
META EMBEDDED SIGNUP TOKEN EXCHANGE
  Meta endpoint: https://graph.facebook.com/v26.0/oauth/access_token
  Method: GET
  App ID: 3862862217342382
  Parameter names: ['client_id', 'client_secret', 'code']
  redirect_uri included: False
  Code length: 451
```

**✅ Success Indicator**: `redirect_uri included: False`
**❌ Failure Indicator**: `redirect_uri included: True`

### Step 2: Test Complete Flow

1. **Clear browser cache and session storage**
2. **Navigate to**: `https://apps.orvym.com/dashboard/integrations`
3. **Click**: "Connect WhatsApp Business"
4. **Complete Meta Embedded Signup**:
   - Select WhatsApp Business Account
   - Select Phone Number
   - Click "Continue" / "Finish"
5. **Monitor browser console** for logs:
   ```
   [EmbeddedSignup] LOGIN_CODE_RECEIVED
   [EmbeddedSignup] READY_FOR_BACKEND_EXCHANGE
   [EmbeddedSignup] BACKEND_EXCHANGE_STARTED
   [EmbeddedSignup] BACKEND_EXCHANGE_SUCCESS
   ```
6. **Check Network tab** for the callback request:
   ```
   POST https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback
   Status: 200 OK
   ```

### Step 3: Verify Success Response

**Expected Success Response**:
```json
{
  "success": true,
  "status": "connected",
  "waba_id": "123456789012345",
  "phone_number_id": "987654321098765",
  "business_id": "456789012345678",
  "phone_registered": true,
  "data": {
    "business_name": "Your Business",
    "phone_number": "+1234567890",
    "phone_number_id": "987654321098765",
    "waba_id": "123456789012345",
    "verified_name": "Your Business Name"
  }
}
```

**Frontend should show**: "WhatsApp connected successfully!"

### Step 4: Verify Integration Saved

1. **Refresh the page**: `https://apps.orvym.com/dashboard/integrations`
2. **Check WhatsApp section** shows:
   - ✅ Status: Connected
   - Phone number displayed
   - Phone Number ID displayed
   - Webhook URL available
   - Verify Token available

---

## Troubleshooting

### If Error 36008 Still Occurs

1. **Check Backend Logs on Render**:
   - Go to Render Dashboard → `orym-saas-application` → Logs
   - Search for: `META EMBEDDED SIGNUP TOKEN EXCHANGE`
   - Verify: `redirect_uri included: False`

2. **If `redirect_uri included: True`**:
   - Backend deployment failed or old code is running
   - Re-deploy backend to Render
   - Clear Render build cache if needed

3. **Check Frontend Console**:
   - Look for: `BACKEND_EXCHANGE_STARTED`
   - Check Network tab for actual payload sent
   - Verify payload does NOT contain `redirect_uri`

4. **If Frontend Sends `redirect_uri`**:
   - Frontend deployment failed
   - Clear browser cache completely
   - Hard refresh (Ctrl+Shift+R)
   - Re-deploy frontend

### Common Issues

**Issue**: "Authorization code already processed"
- **Cause**: Same code submitted twice
- **Fix**: Start a completely new Embedded Signup attempt

**Issue**: "Authorization code expired"
- **Cause**: Code is only valid for 30 seconds
- **Fix**: Complete the flow faster, or start a new attempt

**Issue**: Backend still sends `redirect_uri`
- **Cause**: Old deployment still running
- **Fix**: Force deploy latest commit on Render

---

## Environment Variables

Verify these are set correctly on Render:

```bash
META_APP_ID=3862862217342382
META_APP_SECRET=4e8c221a2b70d959dfd452ab91a51c06
META_CONFIG_ID=2432311603846818
META_OAUTH_REDIRECT_URI=https://apps.orvym.com/dashboard/integrations/
```

**Note**: `META_OAUTH_REDIRECT_URI` is used for verification/configuration endpoints only, NOT for the token exchange.

---

## Success Criteria

✅ The fix is successful when:

1. **Backend logs show**: `redirect_uri included: False`
2. **Meta returns HTTP 200** with business token
3. **No error 36008** in response
4. **Frontend shows**: "WhatsApp connected successfully!"
5. **Integration persisted** in database
6. **WhatsApp messaging** works correctly

---

## Rollback Plan

If issues occur after deployment:

1. **Revert Git Commit**:
   ```bash
   git revert HEAD
   git push origin master
   ```

2. **Manual Rollback on Render**:
   - Go to Render Dashboard → Deployments
   - Find previous working deployment
   - Click "Redeploy"

3. **Contact**: Check Meta App Dashboard for any configuration changes needed

---

## Additional Notes

- **Token exchange is single-use**: Each authorization code can only be exchanged once
- **Code expires in 30 seconds**: Complete the flow quickly
- **Session info is optional**: Backend resolves WABA/Phone IDs server-side if missing
- **Phone registration**: Requires `META_PHONE_REGISTRATION_PIN` environment variable

---

## Next Steps

1. ✅ Code changes verified
2. ⚠️ Deploy backend to Render
3. ⚠️ Deploy frontend to Hostinger (automatic via GitHub Actions)
4. ⚠️ Test complete Embedded Signup flow
5. ⚠️ Verify success in production logs
6. ⚠️ Document any additional issues found

---

**Last Updated**: 2026-08-12
**Status**: Ready for production deployment
