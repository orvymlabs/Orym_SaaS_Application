# Quick Testing Guide

## Testing Meta Embedded Signup Locally

### Prerequisites
- Running backend on port 8001
- Running frontend on port 3000
- ngrok installed (for Meta webhook testing)

### Step 1: Set Up Meta App (Development)

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a test app (Business type)
3. Add WhatsApp product
4. In WhatsApp Configuration, set up Embedded Signup with a test configuration

### Step 2: Configure Backend Environment

```bash
cd backend
```

Edit `.env` file and add:
```env
META_APP_ID=your_test_app_id
META_CONFIG_ID=your_test_config_id
```

### Step 3: Start Backend with Database Fix

```bash
# Fix database sequence if needed
python fix_bot_sequence.py

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Step 4: Start Frontend

```bash
cd frontend
npm run dev
```

### Step 5: Test the Flow

1. Open browser: `http://localhost:3000`
2. Log in to your account
3. Navigate to **Dashboard** → **Integrations** → **WhatsApp** tab
4. You should see the "Connect WhatsApp" button
5. Click the button
6. Facebook login popup should appear
7. Complete the authorization flow
8. Verify the connected state appears with your phone number

### Expected Results

✅ **When Meta is configured:**
- "Connect WhatsApp" button appears
- Clicking launches Facebook SDK popup
- After authorization, credentials are saved automatically
- Connected state shows phone number, status, webhook URL, verify token
- Reconnect and Disconnect buttons are visible

✅ **When Meta is NOT configured:**
- Manual credential entry form appears (fallback)
- All existing functionality works as before

### Testing Disconnect

1. In connected state, click "Disconnect"
2. Confirm the action
3. Credentials are removed
4. "Connect WhatsApp" button appears again
5. All other data (bots, flows, settings) remain intact

### Testing Reconnect

1. In connected state, click "Reconnect"
2. Complete OAuth flow again
3. New credentials replace old ones
4. All bots and settings remain intact

### Troubleshooting Test Issues

**Issue: "Facebook SDK not loaded"**
- Solution: Refresh the page, ensure internet connection

**Issue: "Meta Embedded Signup is not configured"**
- Solution: Check backend/.env has META_APP_ID and META_CONFIG_ID set
- Solution: Restart backend after adding env vars

**Issue: "Failed to exchange authorization code"**
- Solution: Verify META_APP_SECRET is correct
- Solution: Check backend logs for detailed error

**Issue: OAuth popup blocked**
- Solution: Allow popups for localhost in browser settings

### Testing Manual Fallback

To test the manual form fallback:
1. Remove META_APP_ID from .env (or set it to empty string)
2. Restart backend
3. Refresh integrations page
4. Manual credential form should appear

### Verify Backend Endpoints

```bash
# Test Meta config endpoint
curl http://localhost:8001/api/integrations/meta/config \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return: {"app_id": "...", "config_id": "..."}
# Or 500 if not configured
```

## Testing in Production

### Step 1: Deploy Backend

```bash
# Ensure .env has production Meta credentials
META_APP_ID=your_production_app_id
META_CONFIG_ID=your_production_config_id
META_APP_SECRET=your_production_app_secret

# Deploy to your production server
```

### Step 2: Configure Meta App for Production

1. Add your production domain to App Domains
2. Update webhook URL to your production URL
3. Switch app to Live mode
4. Complete App Review if required

### Step 3: Deploy Frontend

```bash
cd frontend
npm run build
# Deploy the out/ or .next/ directory
```

### Step 4: End-to-End Test

1. Go to your production URL
2. Log in
3. Navigate to Integrations
4. Test Connect WhatsApp flow
5. Verify webhook receives test messages

## Verify Everything Works

### Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads without errors
- [ ] "Connect WhatsApp" button appears (if Meta configured)
- [ ] Manual form appears (if Meta NOT configured)
- [ ] OAuth flow completes successfully
- [ ] Credentials saved to database
- [ ] Connected state displays correctly
- [ ] Webhook URL is correct
- [ ] Verify token is generated
- [ ] Reconnect works
- [ ] Disconnect works
- [ ] Existing integrations still work
- [ ] Message sending still works
- [ ] Webhook processing still works

### Database Verification

```sql
-- Check if credentials were saved
SELECT 
    id, 
    bot_id, 
    phone_number_id, 
    whatsapp_number,
    verify_token,
    whatsapp_token IS NOT NULL as has_token
FROM integrations 
WHERE phone_number_id IS NOT NULL;
```

### Log Verification

Check backend logs for:
```
INFO - Successfully setup WhatsApp integration for WABA {waba_id}, phone {display_phone_number}
INFO - Successfully connected WhatsApp for user {user_id}: {display_phone_number}
```

## Quick Demo Script

For demonstrating to stakeholders:

1. **Show Before State** (Not Connected)
   - Open Integrations page
   - Point out the "Connect WhatsApp" button
   
2. **Show Connection Process**
   - Click "Connect WhatsApp"
   - Complete Facebook authorization
   - Show credentials being saved automatically
   
3. **Show After State** (Connected)
   - Show green connected status
   - Show phone number
   - Show webhook URL
   - Show verify token
   
4. **Show Reconnect**
   - Click Reconnect
   - Show it updates credentials seamlessly
   
5. **Compare with Manual Entry**
   - Show how much easier one-click is vs. manual 5-field form

## Performance Testing

- OAuth flow should complete in < 5 seconds
- Token exchange should complete in < 2 seconds
- Page load should be instant (SDK loads async)
- No impact on existing message sending performance

## Security Testing

- [ ] Access tokens are encrypted in database
- [ ] Tokens never appear in frontend console
- [ ] Phone number uniqueness is enforced
- [ ] Authorization code expires after use
- [ ] Webhook signatures are verified
