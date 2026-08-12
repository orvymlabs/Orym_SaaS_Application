# Production Test Checklist - OAuth Redirect URI Fix

## Test Date: _____________
## Tested By: _____________

---

## Pre-Test Verification

- [ ] Confirm backend is deployed to: `https://orym-saas-application.onrender.com`
- [ ] Confirm frontend is deployed to: `https://apps.orvym.com`
- [ ] Check git commits are pushed to `master` branch

---

## Production Test Steps

### Step 1: Start Fresh Embedded Signup
1. [ ] Go to `https://apps.orvym.com/dashboard/integrations`
2. [ ] Click "Connect WhatsApp" button
3. [ ] Meta Embedded Signup popup opens
4. [ ] Complete the Meta onboarding flow

### Step 2: Monitor Browser Console
Open browser DevTools Console and verify these logs appear:

- [ ] `[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup`
- [ ] `[EmbeddedSignup] Config ID: 2432311603846818`
- [ ] `[EmbeddedSignup] LOGIN_CODE_RECEIVED`
- [ ] Code length shown (should be ~451 characters)
- [ ] `[EmbeddedSignup] BACKEND_EXCHANGE_STARTED`
- [ ] `[EmbeddedSignup] BACKEND_EXCHANGE_SUCCESS`

### Step 3: Check Backend Logs (Render Dashboard)
Go to: https://dashboard.render.com → Find service → View Logs

Look for these log entries:

```
META EMBEDDED SIGNUP TOKEN EXCHANGE
  Parameter names: ['client_id', 'client_secret', 'code']
  redirect_uri included: False
  Code length: 451
```

**CRITICAL CHECK**: `redirect_uri included: False`

Then verify success:

```
META GRAPH API RESPONSE:
  Status Code: 200
  Access token received: YES
```

### Step 4: Verify No Error 36008

**✅ SUCCESS** if you see:
- HTTP 200 response
- Token exchange successful
- No error code 100
- No error subcode 36008

**❌ FAILURE** if you see:
- HTTP 400 response
- Error code: 100
- Error subcode: 36008
- Message: "redirect_uri is identical..."

### Step 5: Complete Integration Flow

- [ ] Backend discovers WABA ID
- [ ] Backend discovers Phone Number ID
- [ ] WABA subscription succeeds
- [ ] Phone registration completes (or skips if no PIN configured)
- [ ] Integration saved to database
- [ ] Frontend shows: "WhatsApp connected successfully!"
- [ ] WhatsApp status shows: **CONNECTED**

### Step 6: Persistence Test

- [ ] Refresh the page
- [ ] WhatsApp status still shows: **CONNECTED**
- [ ] Phone number displayed correctly
- [ ] No "Connect WhatsApp" button (since already connected)

---

## Expected Backend Log Flow

```
META OAUTH CALLBACK - POST REQUEST
User ID: [user_id]
Code received: AQxxxxxx...xxxx (length 451)
WABA ID: (NOT provided - session info missing) OR [actual_waba_id]
Phone Number ID: (NOT provided - session info missing) OR [actual_phone_id]
Business ID: (not provided) OR [actual_business_id]

META EMBEDDED SIGNUP TOKEN EXCHANGE
  Meta endpoint: https://graph.facebook.com/v26.0/oauth/access_token
  Method: GET
  App ID: 3862862217342382
  Parameter names: ['client_id', 'client_secret', 'code']
  redirect_uri included: False
  Code length: 451

META GRAPH API RESPONSE:
  Status Code: 200
  Access token received: YES

✅ Token exchange successful

META ACCESS TOKEN VALIDATION
  App ID: 3862862217342382
  Token type: [type]
  Granted scopes: [...]
  Missing WhatsApp scopes: none
  WABA target_ids from granular_scopes: [count] found

[EmbeddedSignup] Step 1/6 - Meta token exchange succeeded
[EmbeddedSignup] Step 2/6 - Token validation succeeded
[EmbeddedSignup] WABA ID resolved: [waba_id]
[EmbeddedSignup] Phone Number ID from session: [phone_id] OR
[EmbeddedSignup] Phone Number ID resolved server-side from the WABA phone_numbers edge: [phone_id]
[EmbeddedSignup] Step 5/6 - WABA validation succeeded
[EmbeddedSignup] Step 6/6 - Phone number verified
[EmbeddedSignup] Step 6/6 - WABA subscription succeeded
[EmbeddedSignup] Phone registration: registered=[true/false] skipped=[true/false]
[EmbeddedSignup] WhatsApp integration setup complete

Successfully connected WhatsApp for user [user_id]: [phone_number] (WABA [waba_id])
```

---

## Success Criteria

✅ **FIX IS WORKING** when ALL of these are true:

1. Backend log shows: `redirect_uri included: False`
2. Meta returns: `Status Code: 200`
3. No error 100 or subcode 36008
4. Token exchange successful
5. WABA discovered
6. Phone number discovered
7. Frontend displays: "WhatsApp connected successfully!"
8. Connection persists after page refresh

---

## Troubleshooting

### If you still see Error 36008:

1. **Check backend deployment**:
   - Is the latest code deployed?
   - Check commit hash on Render matches local
   - Verify no old code is cached

2. **Check the actual request**:
   - Look at backend logs for the EXACT params sent
   - Confirm `redirect_uri included: False`

3. **If redirect_uri is still being sent**:
   - Backend code wasn't deployed
   - Render is serving cached/old version
   - Need to manually deploy latest commit

### If error persists after confirming correct code:

This would indicate a different issue (not redirect_uri). Check:
- Code expiration (30 seconds)
- Duplicate code submission
- Meta App credentials
- App permissions
- Advanced Access requirements

---

## Notes

- Authorization codes are **single-use** and expire in ~30 seconds
- Never retry with the same code
- Each test requires a completely fresh Embedded Signup session
- Check both browser console AND Render backend logs

---

## Test Result

- [ ] ✅ **PASSED** - Error 36008 is completely resolved
- [ ] ❌ **FAILED** - Error 36008 still occurs
- [ ] ⚠️ **PARTIAL** - Different error occurred

**Actual Result**:
```
[Paste error message or success confirmation here]
```

**Additional Notes**:
```
[Add any observations, issues, or recommendations]
```
