FINAL PRODUCTION FIX — META WHATSAPP EMBEDDED SIGNUP

You are fixing the existing production WhatsApp Embedded Signup integration.

DO NOT rebuild the entire integration.
DO NOT introduce a different OAuth architecture.
DO NOT randomly change the Meta flow.
Preserve the existing working Embedded Signup implementation and fix the current regression.

==================================================
CURRENT PRODUCTION APP
==================================================

Frontend:
https://apps.orvym.com

Backend:
https://orym-saas-application.onrender.com

Meta App ID:
3862862217342382

Embedded Signup Config ID:
2432311603846818

CANONICAL REDIRECT URI:
https://apps.orvym.com/dashboard/integrations/

This exact URI must be used everywhere.

==================================================
CURRENT ERROR
==================================================

Frontend successfully receives the Embedded Signup authorization code:

[EmbeddedSignup] exchangeable code received via FB.login callback (length: 451)

But current backend logs show:

Parameter names:
['client_id', 'client_secret', 'code']

redirect_uri included: False

Then Meta returns:

Error code: 100
Error subcode: 36008
Error type: OAuthException

Error message:
Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request

The current frontend also shows:

OAuth callback error:
Error validating verification code

==================================================
CRITICAL EVIDENCE
==================================================

A PREVIOUS VERSION OF THE SAME PRODUCTION SYSTEM SUCCESSFULLY EXCHANGED THE CODE.

The successful log was:

Parameter names:
['client_id', 'client_secret', 'code', 'redirect_uri']

redirect_uri included: True

redirect_uri value:
https://apps.orvym.com/dashboard/integrations/

Meta response:

Status Code: 200
Access token received: YES
Token exchange successful

Therefore:

DO NOT REMOVE redirect_uri.

The current implementation regressed because redirect_uri is currently being omitted.

Restore the previously successful behavior.

==================================================
PART 1 — FIX TOKEN EXCHANGE
==================================================

The backend Meta token exchange MUST send:

GET
https://graph.facebook.com/v26.0/oauth/access_token

with:

client_id=<META_APP_ID>
client_secret=<META_APP_SECRET>
code=<ONE_TIME_AUTHORIZATION_CODE>
redirect_uri=https://apps.orvym.com/dashboard/integrations/

The redirect_uri MUST NOT be omitted.

Do not conditionally remove it.

Do not send an empty string.

Do not send null.

Do not use:

window.location.origin

Do not use:

http://localhost:3000

Do not use:

https://apps.orvym.com/dashboard/integrations

without the trailing slash.

Use exactly:

https://apps.orvym.com/dashboard/integrations/

==================================================
PART 2 — FRONTEND
==================================================

When Embedded Signup returns the authorization code, the frontend must send:

{
  code: "<authorization_code>",
  redirect_uri: "https://apps.orvym.com/dashboard/integrations/"
}

to:

POST
https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback

Do not remove redirect_uri from this request.

Do not calculate a different redirect URI dynamically.

Use one canonical production constant.

The frontend and backend must use exactly the same value.

==================================================
PART 3 — BACKEND
==================================================

Update the callback endpoint so it accepts redirect_uri.

Example request body:

{
  "code": "...",
  "redirect_uri": "https://apps.orvym.com/dashboard/integrations/"
}

Backend validation:

- code is required
- redirect_uri is required
- reject empty redirect_uri
- normalize ONLY if absolutely necessary
- for production, require the canonical exact URI

Then pass that exact redirect_uri to Meta's /oauth/access_token request.

IMPORTANT:

The backend must NOT silently discard redirect_uri.

Current bug:

Frontend sends/knows redirect_uri
        ↓
Backend removes it
        ↓
Meta receives only client_id + client_secret + code
        ↓
36008

Fix this.

==================================================
PART 4 — EMBEDDED SIGNUP FLOW
==================================================

Keep the official Meta Embedded Signup flow.

Current configuration:

App ID:
3862862217342382

Config ID:
2432311603846818

The flow should remain:

User clicks Connect WhatsApp
        ↓
Meta Embedded Signup opens
        ↓
User completes onboarding
        ↓
Meta returns authorization code
        ↓
Frontend sends code + exact redirect_uri
        ↓
Backend exchanges code
        ↓
Meta returns access token
        ↓
WABA discovery
        ↓
Phone number discovery
        ↓
Required WhatsApp onboarding/subscription operations
        ↓
Save integration
        ↓
Dashboard shows WhatsApp connected

Do not stop after receiving the code.

Do not consider the integration successful merely because FB.login returns "connected".

==================================================
PART 5 — REMOVE DUPLICATE CODE EXCHANGE
==================================================

The latest frontend logs show repeated:

setTimeout
J
setTimeout
J
setTimeout
J

This strongly suggests the callback/retry logic can execute repeatedly.

FIX THIS.

The same authorization code must NEVER be sent to the backend multiple times.

Implement a one-time exchange guard.

Requirements:

- once code exchange starts, lock the exchange
- disable repeated callback execution
- do not retry the same authorization code
- do not call the backend repeatedly after HTTP 400
- do not use setTimeout polling to repeatedly exchange the same code
- reset the lock only when starting a completely new Embedded Signup session

The Meta authorization code is short-lived and single-use.

Exchange it exactly once.

==================================================
PART 6 — LOGGING
==================================================

Add safe diagnostic logs.

DO NOT log:

- client_secret
- access_token
- full authorization code

Log:

[EmbeddedSignup] OAuth callback started

Code length: <number>

Frontend redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Backend redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Meta exchange redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Token exchange status:
200 / 400

Meta error code:
...

Meta error subcode:
...

This is required so the exact value can be verified in Render logs.

==================================================
PART 7 — META DASHBOARD
==================================================

Verify that this exact redirect URI is registered in the Meta App configuration:

https://apps.orvym.com/dashboard/integrations/

There must not be a mismatch between:

1. Embedded Signup/OAuth dialog configuration
2. Frontend redirect URI
3. Backend redirect URI
4. Meta Dashboard Valid OAuth Redirect URIs

Use the exact same production URI everywhere.

==================================================
PART 8 — IMPORTANT: DO NOT CONFUSE STEP 1 WITH STEP 2
==================================================

There was a previous test where token exchange succeeded:

Status Code: 200
Access token received: YES
Token exchange successful

After that, the backend failed at:

Step 2/5 — WABA discovery

with:

(#100) Missing Permission

That is a SEPARATE issue.

Do not change the OAuth exchange architecture to solve the WABA permission issue.

First restore:

STEP 1:
authorization code → access token

Then handle:

STEP 2:
access token → WABA discovery

==================================================
PART 9 — WABA DISCOVERY
==================================================

After Step 1 succeeds, continue the existing onboarding flow.

If the current implementation calls:

GET /me/businesses

and Meta returns:

(#100) Missing Permission

DO NOT pretend that OAuth exchange failed.

Instead:

1. Inspect the permissions/scopes actually granted to the returned access token.
2. Verify the Embedded Signup configuration has the required WhatsApp Business permissions.
3. Verify the app has the required permissions/Access levels in Meta.
4. Use the correct WABA discovery mechanism supported by the current Embedded Signup token.
5. Keep the WABA discovery logic separate from OAuth token exchange.
6. Return a clear Step 2 error if permission is genuinely missing.

Do not remove required permissions just to make the API call pass.

==================================================
PART 10 — REQUIRED PERMISSIONS
==================================================

The app currently requests/requires:

whatsapp_business_messaging
whatsapp_business_management
public_profile

Do not remove these from the Embedded Signup flow.

Verify the actual granted permissions on the returned token before calling protected WhatsApp Business endpoints.

==================================================
PART 11 — DO NOT BREAK APP REVIEW
==================================================

The app is preparing for Meta App Review.

Do not modify the integration in a way that breaks:

- WhatsApp Business Messaging
- WhatsApp Business Management
- Embedded Signup
- production OAuth
- customer onboarding

The final flow must be suitable for production and App Review.

==================================================
PART 12 — ACCEPTANCE TEST
==================================================

DO NOT SAY "FIXED" UNTIL ALL OF THESE PASS.

TEST 1:
Open production:

https://apps.orvym.com/dashboard/integrations/

TEST 2:
Click Connect WhatsApp.

TEST 3:
Meta Embedded Signup opens.

TEST 4:
Complete the Meta onboarding flow.

TEST 5:
Frontend receives a code.

TEST 6:
Frontend sends:

code
redirect_uri=https://apps.orvym.com/dashboard/integrations/

TEST 7:
Render logs MUST show:

redirect_uri included: True

redirect_uri value:
https://apps.orvym.com/dashboard/integrations/

TEST 8:
Meta token exchange MUST return:

HTTP 200

Access token received: YES

Token exchange successful

TEST 9:
There must be NO:

Error subcode 36008

TEST 10:
There must be NO duplicate token exchange requests for the same code.

TEST 11:
Backend proceeds to WABA discovery.

TEST 12:
WABA is discovered successfully.

TEST 13:
Phone Number ID is discovered successfully.

TEST 14:
Required WhatsApp subscription/onboarding operations complete successfully.

TEST 15:
Integration is saved against the correct logged-in user.

TEST 16:
Dashboard shows:

WhatsApp Connected

==================================================
VERY IMPORTANT
==================================================

Do not make assumptions.

Do not rewrite working parts unnecessarily.

The previous logs already prove that this exact token exchange works when redirect_uri is included:

client_id
client_secret
code
redirect_uri

with:

https://apps.orvym.com/dashboard/integrations/

Restore this behavior first.

Then fix WABA discovery permissions separately if Step 2 still fails.

FINAL SUCCESS CONDITION:

Embedded Signup must work end-to-end in PRODUCTION:

Meta Embedded Signup
→ authorization code
→ token exchange HTTP 200
→ WABA discovery
→ phone number discovery
→ WhatsApp onboarding/subscription
→ integration saved
→ dashboard connected.

Only after the complete flow passes should the implementation be considered finished.