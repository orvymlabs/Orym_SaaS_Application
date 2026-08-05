# Meta Dashboard Configuration for Production

## Required Changes in Meta App Dashboard

### Step 1: Add Production OAuth Redirect URI

1. Go to: https://developers.facebook.com/apps/3862862217342382/settings/basic/

2. Scroll to **"Valid OAuth Redirect URIs"**

3. Add BOTH URLs (local + production):
   ```
   http://localhost:3000/dashboard/integrations
   https://apps.orvym.com/dashboard/integrations
   ```

4. Click **"Save Changes"**

### Step 2: Configure App Domains

1. In the same Basic Settings page

2. Find **"App Domains"** section

3. Add BOTH domains:
   ```
   localhost
   apps.orvym.com
   ```

4. Click **"Save Changes"**

### Step 3: Configure JavaScript SDK Allowed Domains

1. Go to: **WhatsApp > Configuration** in the left sidebar

2. Find **"Allowed Domains for the JavaScript SDK"**

3. Add BOTH domains:
   ```
   localhost
   apps.orvym.com
   ```

4. Click **"Save"**

### Step 4: Verify Webhook Configuration

1. In WhatsApp > Configuration

2. **Webhook URL** should be:
   ```
   https://orym-saas-application.onrender.com/webhook
   ```

3. **Verify Token** should match what's in your database

## Important Notes:

- ✅ Keep localhost URLs for local development
- ✅ Add production URLs for live site
- ⚠️ URLs must match EXACTLY (including https:// and path)
- ⚠️ No trailing slashes

## Testing Production Configuration:

After saving all changes:

1. Open: https://apps.orvym.com/dashboard/integrations
2. Click "Connect WhatsApp"
3. Meta popup should open
4. Complete authorization
5. Should redirect back to: https://apps.orvym.com/dashboard/integrations
6. WhatsApp should be connected ✅

## Troubleshooting:

**"Redirect URI Mismatch" error:**
- Meta received a different redirect URI than what's configured
- Check the URL in Meta Dashboard matches EXACTLY
- Verify NEXT_PUBLIC_APP_URL is set correctly in frontend

**"App Domain Not Allowed" error:**
- apps.orvym.com is not in App Domains
- Add it and save

**SDK won't load:**
- apps.orvym.com is not in Allowed Domains for JavaScript SDK
- Add it and save
