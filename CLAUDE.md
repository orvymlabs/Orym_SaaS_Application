# FINAL TARGETED FIX — WHATSAPP EMBEDDED SIGNUP OAUTH 36008

We need to fix the CURRENT production failure without breaking any part of the already-working WhatsApp Embedded Signup implementation.

## IMPORTANT: DO NOT REWRITE THE EMBEDDED SIGNUP

The following parts are already working and MUST NOT be changed unnecessarily:

* Facebook SDK initialization
* App ID: `3862862217342382`
* Embedded Signup Config ID: `2432311603846818`
* `FB.login()` with `config_id`
* `response_type=code`
* `override_default_response_type=true`
* `sessionInfoVersion=3`
* existing message listener
* OAuth code extraction
* popup behavior
* existing dashboard integration UI
* existing authentication
* existing WhatsApp/webhook/messaging code
* existing database logic unrelated to this failure

Make the smallest possible targeted change.

---

# CURRENT PRODUCTION FLOW

Frontend logs prove that these steps are working:

```text
Message listener registered
Facebook SDK initialized
Launching WhatsApp Embedded Signup via FB.login popup
Config ID: 2432311603846818
OAuth code detected
LOGIN_CODE_RECEIVED
READY_FOR_BACKEND_EXCHANGE
BACKEND_EXCHANGE_STARTED
```

The OAuth code is successfully received.

The current failure occurs AFTER the code is received.

---

# EXACT CURRENT ERROR

Production frontend:

```text
POST https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback
400 Bad Request
```

Frontend then reports:

```text
OAUTH_REDIRECT_URI_MISMATCH:
OAuth authorization code is invalid or was issued for a different redirect URI.
```

Previous backend logs showed:

```text
Parameter names:
['client_id', 'client_secret', 'code', 'redirect_uri']

redirect_uri included: True

redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Meta response:
HTTP 400
Error code: 100
Error subcode: 36008
Error type: OAuthException

Error message:
Error validating verification code.
Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request
```

This is the exact failure we need to eliminate.

---

# ROOT CAUSE TO FIX

This is the official WhatsApp Embedded Signup `config_id` flow.

Do NOT treat it as a generic Facebook OAuth authorization-code flow.

Do NOT mix a generic OAuth `redirect_uri` exchange into the Embedded Signup business-token exchange.

According to the Meta Tech Provider documentation being used for this implementation, the Embedded Signup Step 1 token exchange is:

```text
GET /oauth/access_token
```

with:

```text
client_id
client_secret
code
```

For THIS Embedded Signup exchange, do NOT send:

```text
redirect_uri
```

Therefore the Meta Graph API request MUST be constructed exactly as:

```python
params = {
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": code,
}
```

NOT:

```python
params = {
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": code,
    "redirect_uri": redirect_uri,
}
```

Do not conditionally append `redirect_uri` either.

For this Embedded Signup code-exchange path, `redirect_uri` must not be sent to Meta.

---

# VERY IMPORTANT: FIX THE FRONTEND TOO

The frontend currently logs:

```text
Frontend redirect_uri:
https://apps.orvym.com/dashboard/integrations/
```

Remove `redirect_uri` from the Embedded Signup backend callback payload as well.

Current conceptual payload:

```javascript
{
    code,
    redirect_uri,
    waba_id,
    phone_number_id,
    business_id
}
```

Change the Embedded Signup payload to:

```javascript
{
    code,
    waba_id,
    phone_number_id,
    business_id
}
```

If `waba_id`, `phone_number_id`, or `business_id` are unavailable, they may remain absent/null because the backend already has a server-side resolution path.

But DO NOT send `redirect_uri` from this Embedded Signup flow.

Do NOT remove or modify redirect URI configuration belonging to unrelated OAuth integrations.

Scope this change ONLY to:

```text
WhatsApp Embedded Signup
→ authorization code
→ backend business-token exchange
```

---

# CRITICAL: AUDIT THE ENTIRE BACKEND PATH

Do not only change one visible line.

Trace the complete call chain:

```text
POST /api/integrations/meta/oauth/callback
        ↓
router
        ↓
Meta OAuth service
        ↓
token exchange helper
        ↓
Graph API request
```

Search the entire codebase for:

```text
redirect_uri
oauth/access_token
oauth_callback
meta/oauth
exchange
exchange_code
client_secret
```

Find every place where `redirect_uri` could be injected.

Make sure that for the WhatsApp Embedded Signup token exchange:

```text
redirect_uri is NOT present
```

even if the frontend accidentally sends one.

The backend should explicitly ignore/reject the unused redirect URI for this specific flow instead of forwarding it to Meta.

---

# IMPORTANT: VERIFY THE DEPLOYED RENDER VERSION

The previous attempted fix did NOT eliminate the production error.

Therefore do NOT assume the code change was deployed.

After making the change:

1. Build the backend.
2. Confirm the changed code is included in the deployed build.
3. Deploy to the actual Render production service:

```text
orym-saas-application.onrender.com
```

4. Confirm Render is running the newest deployment.
5. Add a safe production log immediately before the Meta Graph API request.

The log should show:

```text
META EMBEDDED SIGNUP TOKEN EXCHANGE
parameter names: ['client_id', 'client_secret', 'code']
redirect_uri included: false
```

DO NOT log the actual OAuth code.
DO NOT log the app secret.
DO NOT log the business token.

---

# IMPORTANT: PREVENT OLD CODE FROM BEING USED

Check for:

* duplicate token-exchange functions
* old Meta OAuth service files
* old router imports
* duplicate callback endpoints
* environment/config values that re-add redirect_uri
* helper functions that automatically append redirect_uri
* old deployment/build artifacts
* stale Render deployment

The production endpoint must execute the newly corrected function.

---

# DO NOT REUSE THE SAME OAUTH CODE

Meta Embedded Signup authorization codes are short-lived and single-use.

Every test MUST start a completely new Embedded Signup attempt.

Do NOT:

* retry the same code
* refresh and submit the same code
* automatically retry the same code
* call the callback twice for one code
* exchange the code from multiple React effects

The frontend must guarantee one backend exchange per newly received code.

---

# DUPLICATE CALLBACK PROTECTION

Audit the existing frontend so that:

```text
LOGIN_CODE_RECEIVED
```

causes exactly ONE:

```text
BACKEND_EXCHANGE_STARTED
```

for that code.

Use an in-memory/ref/state guard if required.

Do NOT change the existing Meta message listener unnecessarily.

---

# DO NOT CONFUSE THESE TWO EVENTS

There are two different things:

### 1. OAuth authorization code

Currently received successfully:

```text
containsOAuthCode: true
LOGIN_CODE_RECEIVED
```

### 2. WA_EMBEDDED_SIGNUP session information

Currently:

```text
containsWA_EMBEDDED_SIGNUP: false
containsSessionInfo: false
waba_id present: false
phone_number_id present: false
business_id present: false
```

Do NOT conclude that the OAuth code is invalid simply because the OAuth redirect message itself does not contain WABA/phone IDs.

Do NOT inject fake IDs.

The OAuth code exchange and session asset resolution are separate stages.

Keep the existing server-side resolution mechanism.

---

# AFTER THE TOKEN EXCHANGE SUCCEEDS

Do not stop after receiving HTTP 200.

Continue the existing Tech Provider onboarding flow:

## Step 1

Authorization code:

```text
code
```

↓

Business token:

```text
BUSINESS_TOKEN
```

using:

```text
client_id
client_secret
code
```

ONLY.

## Step 2

Subscribe the app to the customer's WABA:

```text
POST /{WABA_ID}/subscribed_apps
```

using the business token.

Expected successful response:

```json
{
  "success": true
}
```

## Step 3

Register the customer's business phone number when required:

```text
POST /{PHONE_NUMBER_ID}/register
```

using the business token and the existing onboarding PIN mechanism.

## Step 4

Persist the successful integration.

Do not rewrite these existing stages unless a new error proves that one of them is broken.

---

# IMPORTANT ABOUT THE 404

The browser also shows:

```text
Failed to load resource: the server responded with a status of 404
```

Do NOT assume this is the cause of the Meta 36008 error.

Find the exact URL/resource returning 404 in the browser Network tab.

If it is unrelated to:

```text
/api/integrations/meta/oauth/callback
```

do not modify the Embedded Signup code because of it.

The known blocking error is:

```text
POST /api/integrations/meta/oauth/callback
→ 400
→ Meta error 100 / subcode 36008
```

Fix that first.

---

# META CONFIGURATION AUDIT

Do NOT randomly modify Meta App settings.

Verify the existing Embedded Signup configuration:

* App ID is correct
* Config ID is correct
* WhatsApp Embedded Signup configuration is active
* required WhatsApp permissions/access are available
* app domains are configured correctly
* production domain is configured
* current Embedded Signup version/config is compatible

But do NOT change the Config ID or rebuild the flow simply because the backend token exchange is failing.

The OAuth code is already being issued, proving that the Embedded Signup launch is functioning.

---

# REQUIRED TEST

After deployment, perform a completely fresh test.

Expected logs:

```text
Message listener registered
Facebook SDK initialized
Launching WhatsApp Embedded Signup
OAuth code received
READY_FOR_BACKEND_EXCHANGE
BACKEND_EXCHANGE_STARTED

META EMBEDDED SIGNUP TOKEN EXCHANGE
parameter names:
['client_id', 'client_secret', 'code']

redirect_uri included:
false
```

Then Meta MUST return HTTP 200 with the business token.

Expected sequence:

```text
OAuth code
↓
Business token
↓
WABA resolution
↓
Phone number ID resolution
↓
WABA subscribed_apps
↓
Phone registration if required
↓
Integration saved
↓
WhatsApp messaging/webhooks working
```

---

# SUCCESS CRITERIA

The following error must disappear:

```text
Error code: 100
Error subcode: 36008
OAUTH_REDIRECT_URI_MISMATCH
```

Do not declare the task fixed merely because:

* popup opens
* code is received
* frontend says READY_FOR_BACKEND_EXCHANGE

The actual success condition is:

```text
OAuth code
→ business token
→ WABA ID
→ phone_number_id
→ onboarding
→ saved integration
→ WhatsApp messaging/webhooks working
```

---

# FINAL SAFETY REQUIREMENT

This is a targeted production bug fix.

DO NOT:

* rewrite Embedded Signup
* replace FB.login()
* replace Config ID
* introduce a second OAuth implementation
* change the Facebook SDK
* change unrelated authentication
* change dashboard functionality
* change database schema unnecessarily
* change webhook logic
* change messaging logic
* remove Meta permissions
* invent WABA/phone IDs
* bypass Meta
* add a fake fallback

Preserve all currently working behavior.

Only fix the incorrect `redirect_uri` handling in the WhatsApp Embedded Signup token-exchange path and verify the deployed Render backend is actually running the fix.

After this change, provide the exact production log showing whether the Meta `/oauth/access_token` request contains `redirect_uri`.
