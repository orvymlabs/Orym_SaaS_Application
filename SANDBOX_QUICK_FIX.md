# Quick Start: Testing AI Mode in Sandbox

## Current Issue
Your sandbox shows "No cached data" which means the AI has no website information to use.

## Fix in 3 Steps

### Step 1: Add Website URL
1. Open your application
2. Go to **Integration** page
3. Add your website URL:
   - Product business: Enter in "WooCommerce URL"
   - Service business: Enter in "WordPress URL"
4. Click **Save**

### Step 2: Fetch Website Content
1. Still on Integration page
2. Click **"Fetch Website Content"** button
3. Wait for success message
4. Verify it shows your site name and data count

### Step 3: Test in Sandbox
1. Go to **Bot Engine** page
2. Set Mode to **"AI"**
3. Add your **API Key** (OpenRouter/OpenAI)
4. Click **Save**
5. Test with: "What is your phone number?"

## What Was Fixed

### Before:
```python
# Sandbox used hardcoded test data
contact_info_data = {"site_name": "Test Store"}
```
❌ AI had no real data to answer questions

### After:
```python
# Sandbox now uses your cached website data
cache = db.query(SiteInfoCache).filter(SiteInfoCache.bot_id == bot.id).first()
if cache:
    contact_info_data = {
        "site_name": cache.site_name,
        "services": cache.services,
        "phone": cache.phone,
        "email": cache.email,
        # ... all your website data
    }
```
✅ AI now has access to your actual website content

## Verify It's Working

Run diagnostic:
```bash
cd backend
python test_ai_mode.py
```

Should show:
- ✅ Website URL configured
- ✅ Website data cached
- ✅ Bot in AI mode
- ✅ API key configured

## Test Questions

Once setup is complete, test with:
1. "What is your phone number?" → Should show your actual phone
2. "What services do you offer?" → Should list your services
3. "Tell me about your business" → Should use your about text

## Still Not Working?

Check:
1. Website URL is correct and accessible
2. "Fetch Website Content" completed successfully
3. Bot mode is set to "AI" (not "Default")
4. API key is valid and has credits
5. Run `python test_ai_mode.py` to see detailed status
