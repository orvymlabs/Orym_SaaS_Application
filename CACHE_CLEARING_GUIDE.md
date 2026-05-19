# Cache Clearing Guide

## If Your Changes Don't Show Immediately

When you update bot settings (form label, templates, etc.) and they don't appear in WhatsApp, follow these steps:

### 1. Backend Cache (Automatic)
✅ Already handled - backend clears cache automatically when you save settings

### 2. Database Session Cache
✅ Already handled - added `db.expire_all()` to force fresh database reads

### 3. Browser Cache
**Clear your browser cache:**
- Chrome: Ctrl+Shift+Delete → Clear cached images and files
- Or: Hard refresh with Ctrl+F5
- Or: Open in Incognito/Private mode

### 4. WhatsApp Cache
**WhatsApp caches bot responses. To clear:**

**Option A: Wait**
- WhatsApp cache expires after ~5 minutes
- Just wait and try again

**Option B: Force Refresh**
- Close WhatsApp completely
- Reopen WhatsApp
- Type "menu" again

**Option C: Use Different Text**
- Instead of "menu", type "Menu" or "MENU"
- WhatsApp treats these as different messages

**Option D: Clear WhatsApp Data (Mobile)**
- Settings → Storage → Clear Cache
- This clears all WhatsApp cache

### 5. Test with Fresh Message
Instead of typing "menu" repeatedly, try:
```
menu
Menu
MENU
show menu
display menu
```

Each variation is treated as a new message by WhatsApp.

### 6. Verify Settings Were Saved

**Check in Dashboard:**
1. Go to Bot Settings → Order Form Settings
2. Refresh the page (F5)
3. Check if your changes are there

**Check via API:**
```bash
curl http://localhost:8001/api/bots/order-form/settings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check in Database:**
```bash
cd backend
python -c "
from database import SessionLocal
from models import BotSettings
db = SessionLocal()
s = db.query(BotSettings).first()
print(f'form_menu_label: {s.form_menu_label}')
print(f'order_form_enabled: {s.order_form_enabled}')
db.close()
"
```

### 7. Force Backend Reload

If nothing works, restart the backend:
```bash
# Stop the backend (Ctrl+C in the terminal)
# Then restart:
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 8. Common Issues

**Issue: "I updated the label but still see old text"**
- Solution: Wait 5 minutes for WhatsApp cache to expire
- Or: Use a different variation of "menu"

**Issue: "Changes show in dashboard but not in WhatsApp"**
- Solution: Clear WhatsApp cache or wait 5 minutes

**Issue: "Nothing shows in menu at all"**
- Check: Form Menu Label field is not empty
- Check: Enable Order Form toggle is ON
- Check: You're logged in with correct account

### 9. Best Practice

After updating settings:
1. Save in dashboard
2. Wait 10 seconds
3. Refresh dashboard page to verify
4. Wait 5 minutes before testing in WhatsApp
5. Or use a different message variation

### 10. Debugging

If still not working, check logs:
```bash
# Backend logs
tail -f backend/logs/app.log

# Or check console output where backend is running
```

Look for:
- "Settings saved for bot X"
- "Cache cleared for bot X"
- Any error messages
