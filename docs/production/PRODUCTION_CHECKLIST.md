# Production Deployment Checklist for Meta Embedded Signup

## 📋 Complete Production Setup Guide

Follow these steps in order to enable Meta Embedded Signup in production.

---

## ✅ Prerequisites

- [ ] You have access to Render dashboard (backend)
- [ ] You have access to Meta Developer Dashboard
- [ ] You have access to deploy frontend (Netlify/Vercel)
- [ ] Backend is already deployed on Render
- [ ] Frontend code is ready (already configured)

---

## 🚀 Step-by-Step Production Setup

### Step 1: Configure Render Backend (15 minutes)

**Current Status:** ❌ Meta credentials missing on production backend

**What to do:**

1. Go to: https://dashboard.render.com
2. Select service: `orym-saas-application`
3. Click **"Environment"** tab
4. Add these environment variables:

   ```
   META_APP_ID=3862862217342382
   META_CONFIG_ID=2432311603846818
   META_APP_SECRET=4e8c221a2b70d959dfd452ab91a51c06
   ```

5. Click **"Save Changes"**
6. Wait for automatic redeploy (~5 minutes)

**Verify it worked:**
```bash
curl https://orym-saas-application.onrender.com/api/integrations/meta/config
```

**Expected result:**
```json
{"app_id":"3862862217342382","config_id":"2432311603846818"}
```

**If you get an error:** The credentials aren't saved yet. Try again.

📄 **Detailed guide:** `PRODUCTION_RENDER_CONFIG.md`

---

### Step 2: Configure Meta Dashboard (10 minutes)

**Current Status:** ⚠️ Likely only has localhost configured

**What to do:**

1. Go to: https://developers.facebook.com/apps/3862862217342382/settings/basic/

2. **Add Production OAuth Redirect URI:**
   - Section: "Valid OAuth Redirect URIs"
   - Add: `https://apps.orvym.com/dashboard/integrations`
   - Keep: `http://localhost:3000/dashboard/integrations` (for local dev)
   - Save

3. **Add Production App Domain:**
   - Section: "App Domains"
   - Add: `apps.orvym.com`
   - Keep: `localhost`
   - Save

4. Go to: **WhatsApp > Configuration**

5. **Add Production JavaScript SDK Domain:**
   - Section: "Allowed Domains for the JavaScript SDK"
   - Add: `apps.orvym.com`
   - Keep: `localhost`
   - Save

6. **Verify Webhook (should already be set):**
   - Webhook URL: `https://orym-saas-application.onrender.com/webhook`
   - Verify Token: (from your database)

📄 **Detailed guide:** `PRODUCTION_META_CONFIG.md`

---

### Step 3: Deploy Frontend (Optional - if not deployed yet)

**Current Status:** ✅ Code is ready, environment variables are configured

**Frontend `.env` is already set for production:**
```env
NEXT_PUBLIC_API_URL=https://orym-saas-application.onrender.com
NEXT_PUBLIC_APP_URL=https://apps.orvym.com
```

**If frontend is already deployed:** Skip this step

**If you need to deploy:**

Choose one:

**Option A: Netlify**
1. Connect repository
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Deploy

**Option B: Vercel**
1. Import repository
2. Root directory: `frontend`
3. Deploy

📄 **Detailed guide:** `PRODUCTION_FRONTEND_DEPLOY.md`

---

### Step 4: Test Production Setup (5 minutes)

**Test 1: Backend Meta Config**
```bash
curl https://orym-saas-application.onrender.com/api/integrations/meta/config
```
✅ Should return: `{"app_id":"...","config_id":"..."}`

**Test 2: Frontend Loads**
1. Open: https://apps.orvym.com
2. ✅ Should load the login page or dashboard

**Test 3: Meta Embedded Signup Works**
1. Go to: https://apps.orvym.com/dashboard/integrations
2. Log in if needed
3. Go to WhatsApp tab
4. ✅ Should see "Connect WhatsApp" button (not manual form)
5. Click the button
6. ✅ Meta popup should open
7. Complete authorization
8. ✅ Should redirect back to integrations page
9. ✅ WhatsApp should be connected

**If any test fails, see Troubleshooting section below**

---

## 📊 Current Status Summary

### Local Development: ✅ READY
- ✅ Backend running: `http://localhost:8001`
- ✅ Frontend running: `http://localhost:3000`
- ✅ Meta credentials configured
- ✅ Code fixed (no errors)
- ✅ Manual form removed
- ⏳ Needs: Meta Dashboard localhost OAuth configuration

### Production: ⏳ PENDING
- ⏳ Backend: Meta credentials need to be added to Render
- ✅ Frontend: Code is ready for deployment
- ⏳ Meta Dashboard: Production OAuth redirect needs configuration
- ⏳ Testing: Pending after configuration

---

## 🔧 Quick Reference

### Production URLs:
- **Frontend:** https://apps.orvym.com
- **Backend API:** https://orym-saas-application.onrender.com
- **Webhook:** https://orym-saas-application.onrender.com/webhook
- **Meta Config:** https://orym-saas-application.onrender.com/api/integrations/meta/config

### Meta Credentials:
- **App ID:** 3862862217342382
- **Config ID:** 2432311603846818
- **App Secret:** 4e8c221a2b70d959dfd452ab91a51c06

### OAuth Redirect URIs (add both):
- Local: `http://localhost:3000/dashboard/integrations`
- Production: `https://apps.orvym.com/dashboard/integrations`

---

## ⚠️ Troubleshooting

### Problem: "Meta Embedded Signup is not configured" in production

**Cause:** Render backend doesn't have Meta credentials

**Fix:**
1. Go to Render dashboard
2. Add META_APP_ID, META_CONFIG_ID, META_APP_SECRET
3. Wait for redeploy
4. Test: `curl https://orym-saas-application.onrender.com/api/integrations/meta/config`

---

### Problem: OAuth redirect fails with "Redirect URI Mismatch"

**Cause:** Meta Dashboard doesn't have production redirect URI

**Fix:**
1. Go to Meta Dashboard → Basic Settings
2. Add: `https://apps.orvym.com/dashboard/integrations` to Valid OAuth Redirect URIs
3. Make sure it's EXACTLY this URL (no trailing slash)
4. Save and try again

---

### Problem: "Facebook SDK not loaded" error

**Cause:** JavaScript SDK domain not allowed

**Fix:**
1. Go to Meta Dashboard → WhatsApp → Configuration
2. Add: `apps.orvym.com` to Allowed Domains for JavaScript SDK
3. Save and refresh browser

---

### Problem: Manual form shows instead of "Connect WhatsApp" button

**Cause:** Frontend can't load Meta config from backend

**Fix:**
1. Check browser console for errors
2. Verify backend returns Meta config (see curl command above)
3. If backend returns error, add credentials to Render

---

## 📝 Documentation Files

- `PRODUCTION_RENDER_CONFIG.md` - Render backend setup
- `PRODUCTION_META_CONFIG.md` - Meta Dashboard configuration
- `PRODUCTION_FRONTEND_DEPLOY.md` - Frontend deployment
- `SETUP_COMPLETE.md` - Local development summary
- `META_SETUP_GUIDE.md` - Detailed local setup guide

---

## ✅ Success Criteria

You'll know it's working when:

1. ✅ Backend returns Meta config: 
   ```bash
   curl https://orym-saas-application.onrender.com/api/integrations/meta/config
   ```

2. ✅ Frontend loads at: https://apps.orvym.com

3. ✅ Integrations page shows "Connect WhatsApp" button (not manual form)

4. ✅ Clicking button opens Meta popup

5. ✅ After authorization, WhatsApp is connected

---

## 🎯 Estimated Time

- **Step 1 (Render):** 15 minutes (including redeploy wait time)
- **Step 2 (Meta Dashboard):** 10 minutes
- **Step 3 (Frontend Deploy):** Skip if already deployed
- **Step 4 (Testing):** 5 minutes

**Total:** ~30 minutes to get production working

---

## 🚀 Ready to Start?

1. Start with Step 1 (Render backend)
2. Then Step 2 (Meta Dashboard)
3. Skip Step 3 if frontend is deployed
4. Finish with Step 4 (testing)

**Questions?** Check the detailed guides in the documentation files listed above.

---

**Last Updated:** 2026-08-05
**Status:** Ready for production deployment
