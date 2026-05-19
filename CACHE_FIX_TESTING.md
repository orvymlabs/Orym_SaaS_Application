# Cache Fix Applied - How to Test

## Changes Made

### 1. Database Session Cache Clearing
✅ Added `db.expire_all()` after every settings save
✅ Added `db.expire()` + `db.refresh()` when reading bot settings
✅ This forces fresh database reads every time

### 2. In-Memory Cache Clearing
✅ `clear_cache_for_bot()` already called after saves
✅ This clears the bot engine's internal cache

## How to Test Your Updates

### Step 1: Update Your Settings
1. Go to Dashboard: http://localhost:3000
2. Login with your account
3. Go to: Bot Settings → Order Form Settings
4. Change "Form Menu Label" to something new (e.g., "Book Appointment")
5. Click Save

### Step 2: Verify Save Was Successful
Refresh the page (F5) and check if your new label is there.

### Step 3: Test in WhatsApp (Choose One Method)

**Method A: Wait for Cache Expiry (Recommended)**
- Wait 5 minutes
- Type "menu" in WhatsApp
- Should show your new label

**Method B: Use Different Message Variation**
Instead of typing "menu" again, try:
```
Menu
MENU
show menu
display menu
```
Each variation bypasses WhatsApp's cache.

**Method C: Clear WhatsApp Cache**
- Close WhatsApp completely
- Reopen WhatsApp
- Type "menu"

### Step 4: Verify It's Working

Your menu should now show:
```
*Main Menu*

• Your Template 1
• Your Template 2
• Book Appointment    ← Your new label

Type the name of any option to continue!
```

## If Still Not Working

### Check 1: Verify Database Was Updated
```bash
cd backend
python -c "
from database import SessionLocal
from models import BotSettings
db = SessionLocal()
s = db.query(BotSettings).first()
print(f'Current label: {s.form_menu_label}')
db.close()
"
```

### Check 2: Check Backend Logs
Look at the terminal where backend is running. You should see:
```
Settings saved for bot X
Cache cleared for bot X
```

### Check 3: Test with Fresh Session
1. Open WhatsApp in a different browser (or incognito mode)
2. Or test with a different phone number
3. Type "menu"

### Check 4: Restart Backend (Last Resort)
```bash
# Stop backend (Ctrl+C)
# Restart:
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## Why Cache Issues Happen

1. **WhatsApp Cache**: WhatsApp caches responses for ~5 minutes
2. **Browser Cache**: Your browser caches the dashboard
3. **Database Session Cache**: SQLAlchemy caches objects (NOW FIXED)
4. **In-Memory Cache**: Bot engine caches settings (NOW FIXED)

## Best Practice Going Forward

After updating settings:
1. Save in dashboard
2. Refresh dashboard page to verify (F5)
3. Wait 5 minutes OR use different message variation
4. Test in WhatsApp

## Quick Test Command

Run this to see current settings:
```bash
curl http://localhost:8001/api/bots/order-form/settings \
  -H "Authorization: Bearer YOUR_TOKEN" | python -m json.tool
```

## Status

✅ Backend cache clearing: FIXED
✅ Database session cache: FIXED
⏳ WhatsApp cache: User must wait or use workaround
⏳ Browser cache: User must refresh page
