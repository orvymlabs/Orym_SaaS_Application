# Frontend Production Deployment Guide

## Current Configuration Status

**Local Development (`.env.local`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
NEXT_PUBLIC_WEBHOOK_URL=http://localhost:8001/webhook
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENV=development
```

**Production (`.env`):**
```env
NEXT_PUBLIC_API_URL=https://orym-saas-application.onrender.com
NEXT_PUBLIC_WS_URL=wss://orym-saas-application.onrender.com
NEXT_PUBLIC_WEBHOOK_URL=https://orym-saas-application.onrender.com/webhook
NEXT_PUBLIC_APP_URL=https://apps.orvym.com
NEXT_PUBLIC_ENV=production
```

## ✅ Good News!

Your frontend `.env` file is already configured for production! ✅

The `.env.local` file only affects local development and won't be deployed.

## Deployment Instructions

### Option A: Deploying to Netlify

1. **Connect Repository:**
   - Go to: https://app.netlify.com/
   - Click "Add new site" → "Import an existing project"
   - Connect your GitHub/GitLab repository
   - Select the `frontend` directory as the base directory

2. **Build Settings:**
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: .next
   ```

3. **Environment Variables:**
   Netlify will automatically use your `.env` file, but you can also add them in the UI:
   - Go to: Site settings → Environment variables
   - Add all `NEXT_PUBLIC_*` variables from `.env`

4. **Deploy:**
   - Click "Deploy site"
   - Wait for build to complete
   - Your site will be live at: `https://your-site.netlify.app`

5. **Custom Domain (if using apps.orvym.com):**
   - Go to: Domain settings
   - Add custom domain: `apps.orvym.com`
   - Configure DNS according to Netlify's instructions

### Option B: Deploying to Vercel

1. **Connect Repository:**
   - Go to: https://vercel.com/
   - Click "Add New" → "Project"
   - Import your repository
   - Select the `frontend` directory

2. **Build Settings:**
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   ```

3. **Environment Variables:**
   Vercel will use your `.env` file automatically

4. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Your site will be live at: `https://your-project.vercel.app`

5. **Custom Domain:**
   - Go to: Project Settings → Domains
   - Add `apps.orvym.com`
   - Configure DNS

## Important: After Deployment

### 1. Verify Frontend Loads Correctly

Visit: `https://apps.orvym.com`

Should see the login page or dashboard (if logged in)

### 2. Test API Connection

1. Open browser console (F12)
2. Navigate to: `https://apps.orvym.com/dashboard/integrations`
3. Check Network tab
4. Should see successful API calls to: `https://orym-saas-application.onrender.com`

### 3. Test Meta Config Loading

In browser console, check:
```javascript
fetch('https://orym-saas-application.onrender.com/api/integrations/meta/config')
  .then(r => r.json())
  .then(console.log)
```

Should return:
```json
{"app_id":"3862862217342382","config_id":"2432311603846818"}
```

If you get an error, the Render backend doesn't have Meta credentials yet.

## Troubleshooting

### Issue: "Failed to fetch" errors

**Cause:** CORS issues or backend not responding

**Fix:**
1. Verify backend is running: `https://orym-saas-application.onrender.com/health`
2. Check CORS settings in `backend/main.py`
3. Ensure `apps.orvym.com` is in `ALLOWED_ORIGINS`

### Issue: Meta Embedded Signup button doesn't show

**Cause:** Frontend can't load Meta config from backend

**Fix:**
1. Check browser console for errors
2. Verify: `https://orym-saas-application.onrender.com/api/integrations/meta/config`
3. Add Meta credentials to Render (see PRODUCTION_RENDER_CONFIG.md)

### Issue: OAuth redirect fails

**Cause:** Redirect URI not configured in Meta Dashboard

**Fix:**
1. Go to Meta Dashboard
2. Add `https://apps.orvym.com/dashboard/integrations` to Valid OAuth Redirect URIs
3. See PRODUCTION_META_CONFIG.md for details

## Files That Control Production

- ✅ `.env` - Production environment variables (committed to Git)
- ❌ `.env.local` - Local development only (not deployed)
- ✅ `next.config.js` - Build configuration

## Environment Variable Priority

```
.env.local (highest - local dev only)
↓
.env.production (production builds)
↓
.env (fallback - used in production)
```

Since `.env.local` is not deployed, production will use `.env` which is already correctly configured.

## Next Steps

1. ✅ Frontend code is ready for production
2. ✅ Environment variables are configured
3. ⏳ Deploy to Netlify/Vercel
4. ⏳ Configure custom domain (if needed)
5. ⏳ Test the deployment
6. ⏳ Configure Meta Dashboard with production URLs
