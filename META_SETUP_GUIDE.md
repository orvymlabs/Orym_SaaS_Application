# Meta Embedded Signup - Complete Setup Guide

## ✅ What's Already Done

1. **Backend Configuration**
   - ✅ Meta credentials configured in `backend/.env`
   - ✅ Backend running on `http://localhost:8001`
   - ✅ Meta config endpoint working: `/api/integrations/meta/config`
   - ✅ OAuth callback handler implemented

2. **Frontend Updates**
   - ✅ Manual setup form REMOVED
   - ✅ Only Meta Embedded Signup button shows
   - ✅ Facebook SDK properly initialized
   - ✅ OAuth flow implemented
   - ✅ Frontend configured to call local backend

## 🔧 Required: Meta App Dashboard Configuration

### Step 1: Configure OAuth Redirect URI

1. Go to: https://developers.facebook.com/apps/3862862217342382/settings/basic/
2. Scroll down to **"Valid OAuth Redirect URIs"** section
3. Add the following URL:
   ```
   http://localhost:3000/dashboard/integrations
   ```
4. Click **"Save Changes"**

**Important:** Meta may require HTTPS for OAuth redirects. If localhost doesn't work, you'll need to use ngrok (see Option B below).

### Step 2: Configure App Domains

1. In the same Basic Settings page
2. Find **"App Domains"** section
3. Add:
   ```
   localhost
   ```
4. Click **"Save Changes"**

### Step 3: Configure JavaScript SDK Allowed Domains

1. Go to: WhatsApp > Configuration in the left sidebar
2. Find **"Allowed Domains for the JavaScript SDK"**
3. Add:
   ```
   localhost
   ```
4. Click **"Save"**

## 🚀 How to Test

### 1. Start the Backend (if not running)
```bash
cd backend
python main.py
```

Backend should be running on: `http://localhost:8001`

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

Frontend should be running on: `http://localhost:3000`

### 3. Test the Flow

1. Open browser: `http://localhost:3000/dashboard/integrations`
2. Log in with your account
3. Go to the WhatsApp tab
4. You should see: **"Connect WhatsApp Business"** button
5. Click the button
6. Meta Embedded Signup popup should open
7. Complete the Meta authorization
8. You'll be redirected back to the integrations page
9. Your WhatsApp should be connected ✅

## 🔍 Troubleshooting

### Issue: "Facebook SDK not loaded"
- **Solution:** Refresh the page
- Check browser console for errors
- Verify internet connection (SDK loads from Meta CDN)

### Issue: "Meta Embedded Signup is not configured"
- **Solution:** Backend is not running or missing credentials
- Verify backend is running: `curl http://localhost:8001/api/integrations/meta/config`
- Should return: `{"app_id":"3862862217342382","config_id":"2432311603846818"}`

### Issue: OAuth redirect fails or shows error
- **Solution:** Check Meta App Dashboard configuration
- Verify OAuth Redirect URI is EXACTLY: `http://localhost:3000/dashboard/integrations`
- Make sure App Domains includes `localhost`

### Issue: Meta requires HTTPS
If Meta doesn't accept `http://localhost`, use **Option B: ngrok**

## 📡 Option B: Using ngrok for HTTPS (If localhost doesn't work)

### 1. Install ngrok
Download from: https://ngrok.com/download

### 2. Expose Frontend via ngrok
```bash
ngrok http 3000
```

You'll get an HTTPS URL like: `https://abc123.ngrok-free.dev`

### 3. Update Frontend Configuration
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_APP_URL=https://abc123.ngrok-free.dev
```

### 4. Update Meta App Dashboard

**Valid OAuth Redirect URIs:**
```
https://abc123.ngrok-free.dev/dashboard/integrations
```

**App Domains:**
```
abc123.ngrok-free.dev
```

**JavaScript SDK Allowed Domains:**
```
abc123.ngrok-free.dev
```

### 5. Access via ngrok URL
Open: `https://abc123.ngrok-free.dev/dashboard/integrations`

## 📋 Current Configuration

**Backend:**
- URL: `http://localhost:8001`
- Meta App ID: `3862862217342382`
- Meta Config ID: `2432311603846818`
- Status: ✅ Running

**Frontend:**
- URL: `http://localhost:3000`
- API URL: `http://localhost:8001`
- Status: Ready to start

**Meta App:**
- App ID: `3862862217342382`
- Config ID: `2432311603846818`
- OAuth Redirect: ⚠️ **Needs to be configured in Meta Dashboard**

## 🎯 Next Steps

1. ✅ Backend is running
2. ✅ Frontend code is fixed
3. ⏳ **Configure OAuth Redirect URI in Meta Dashboard** (Step 1 above)
4. ⏳ **Start the frontend** (`npm run dev`)
5. ⏳ **Test the connection**

## 📞 Support

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check backend logs for API errors
3. Verify all Meta Dashboard settings match exactly
4. Try using ngrok if localhost doesn't work

---

**Last Updated:** 2026-08-05
**Status:** Ready for testing after Meta Dashboard configuration
