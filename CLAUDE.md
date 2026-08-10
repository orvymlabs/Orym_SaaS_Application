FINAL PRODUCTION REBUILD — WHATSAPP EMBEDDED SIGNUP
ORVYM NEXUS / ORVYM LABS

This has been debugged for several days and we are no longer accepting incremental patches.

Rebuild/stabilize the Meta WhatsApp Embedded Signup integration into ONE deterministic production flow.

DO NOT keep changing between different OAuth strategies.
DO NOT add random retries.
DO NOT remove/add redirect_uri blindly.
DO NOT use /me/businesses as the primary WABA discovery mechanism.
DO NOT create fake WABA IDs.
DO NOT use the developer's own WABA for customers.
DO NOT create another parallel OAuth implementation.

The goal is a REAL production-ready Embedded Signup integration.

==================================================
CURRENT PRODUCTION CONFIGURATION
==================================================

Frontend:
https://apps.orvym.com

Integration page:
https://apps.orvym.com/dashboard/integrations/

Backend:
https://orym-saas-application.onrender.com

Meta App ID:
3862862217342382

Embedded Signup Config ID:
2432311603846818

Graph API:
v26.0

Canonical redirect URI:
https://apps.orvym.com/dashboard/integrations/

==================================================
WHAT IS ALREADY WORKING
==================================================

1. Facebook JS SDK initializes successfully.
2. Embedded Signup opens successfully.
3. Meta Config ID is accepted.
4. User reaches the Meta Embedded Signup flow.
5. Meta returns an exchangeable authorization code.
6. Code length is approximately 451 characters.
7. Backend receives the code.
8. MOST IMPORTANT:
   The token exchange has previously succeeded.

Production Render logs previously showed:

Status Code: 200
Access token received: YES
Token exchange successful

Therefore:

APP ID is valid.
APP SECRET is valid.
CONFIG ID is valid.
Authorization code is valid.
Backend can communicate with Meta.

DO NOT BREAK THIS WORKING PART AGAIN.

==================================================
CRITICAL PRESERVATION RULE
==================================================

The implementation previously achieved HTTP 200 and received an access token when the canonical redirect URI was included.

DO NOT modify or remove this working token-exchange behavior unless you can prove from the actual Meta authorization flow/configuration that the authorization code was generated with a different redirect URI.

Preserve the last known working token-exchange implementation while fixing the remaining Embedded Signup flow.

Do NOT switch back to redirect_uri omitted merely because another implementation previously used it.

Do NOT make changes based only on assumptions.

Inspect the actual authorization request, generated authorization code flow, redirect URI, and Meta configuration before changing the token exchange.

The final implementation must have ONE consistent token exchange implementation.

==================================================
PROBLEM 1 — OAUTH 36008
==================================================

Current error:

Error Code: 100
Error Subcode: 36008

Error validating verification code.
Please make sure your redirect_uri is identical to the one used in the OAuth dialog request.

The implementation has previously switched between:

A)
redirect_uri omitted

and

B)
redirect_uri included.

The known successful token exchange used:

client_id
client_secret
code
redirect_uri

with:

https://apps.orvym.com/dashboard/integrations/

and Meta returned:

HTTP 200
Access token received: YES

Therefore, do NOT blindly revert to the implementation that omits redirect_uri.

For the current production authorization-code flow, use ONE canonical redirect URI consistently.

Canonical URI:

https://apps.orvym.com/dashboard/integrations/

It must be identical everywhere.

NO:
http://localhost:3000

NO:
https://apps.orvym.com/dashboard/integrations

NO:
https://apps.orvym.com/dashboard/integrations//

NO:
Render backend URL

YES ONLY:

https://apps.orvym.com/dashboard/integrations/

==================================================
OAUTH IMPLEMENTATION RULE
==================================================

Create ONE shared canonical redirect URI configuration.

Frontend and backend must NOT independently construct different values.

Frontend:
CANONICAL_REDIRECT_URI

Backend:
CANONICAL_REDIRECT_URI

Both must resolve to:

https://apps.orvym.com/dashboard/integrations/

The token exchange must use the same value for the currently verified authorization-code flow.

Expected request:

GET

https://graph.facebook.com/v26.0/oauth/access_token

Parameters:

client_id
client_secret
code
redirect_uri

redirect_uri:

https://apps.orvym.com/dashboard/integrations/

Log:

redirect_uri included: true
redirect_uri value:
https://apps.orvym.com/dashboard/integrations/

Expected result:

HTTP 200
access_token present

==================================================
CRITICAL — REMOVE DUPLICATE CODE EXCHANGE
==================================================

The frontend logs previously showed repeated setTimeout calls.

This suggests retry behavior.

THIS MUST BE REMOVED.

Meta authorization codes are single-use and short-lived.

Implement:

isExchangeInProgress

and a processed-code guard.

Rules:

1. A fresh authorization code can only be submitted ONCE.
2. The same code must NEVER be submitted twice.
3. Disable Connect button while exchange is running.
4. Clear code from client state immediately after submission.
5. Do not retry the same code.
6. If exchange fails, require a NEW Embedded Signup authorization code.
7. Never use setTimeout retries for OAuth exchange.
8. Never call the callback twice for the same FB.login response.
9. Never run OAuth exchange from both:
   - FB.login callback
   - redirect handler
   at the same time.

There must be ONE owner of the authorization-code exchange.

==================================================
FINAL NON-NEGOTIABLE TOKEN EXCHANGE RULE
==================================================

There must be ONE and only ONE production token-exchange implementation.

Search the entire repository and identify:

- where FB.login is launched
- where authorization code is received
- where redirect_uri is determined
- where backend callback is called
- where oauth/access_token is called

Then remove conflicting implementations.

Do not create a second OAuth flow as a workaround.

The final implementation must preserve the previously verified HTTP 200 token exchange and then correctly continue to WABA/phone onboarding.

==================================================
PROBLEM 2 — WABA DISCOVERY
==================================================

The previous implementation did:

GET:
/me/businesses

and failed with:

(#100) Missing Permission

This caused:

[EmbeddedSignup] Step 2/5 failed - WABA discovery

DO NOT make /me/businesses the primary WABA discovery mechanism.

Instead use the official Embedded Signup session information flow.

The Embedded Signup session event should be the source of truth for the customer onboarding session whenever Meta provides it.

==================================================
CRITICAL — VERIFY EMBEDDED SIGNUP SESSION EVENT
==================================================

Before implementing or changing WABA discovery, prove from the production browser logs that Meta actually sends the Embedded Signup session-information message after the user completes the Meta flow.

Listen for:

WA_EMBEDDED_SIGNUP

Handle relevant events:

FINISH
FINISH_ONLY_WABA
ERROR

For debugging, log ONLY:

- event type
- non-sensitive WABA ID
- non-sensitive phone_number_id
- non-sensitive business ID/businessId
- whether the event was received

NEVER log:

- access tokens
- client secrets
- authorization codes
- other credentials

If the WA_EMBEDDED_SIGNUP session event is NOT received:

DO NOT invent another WABA discovery mechanism.

DO NOT fall back to /me/businesses simply to make the flow continue.

Instead:

1. Diagnose why the Embedded Signup session event is missing.
2. Verify the actual Meta Embedded Signup configuration.
3. Verify sessionInfoVersion and other configuration parameters against the existing Meta configuration.
4. Verify the message listener is registered BEFORE Embedded Signup starts.
5. Verify the listener accepts only the expected Facebook-originated message.
6. Confirm the actual event payload structure from production logs without exposing sensitive credentials.
7. Fix the missing session event before changing WABA discovery.

==================================================
FRONTEND EMBEDDED SIGNUP
==================================================

Use ONE implementation.

Use the existing Meta Config ID:

2432311603846818

The implementation must remain aligned with the actual Meta configuration.

If the current configuration requires:

response_type: "code"
override_default_response_type: true

then preserve those settings.

If extras are required, use the actual configuration-supported values.

DO NOT invent a solutionID.

Read the existing Meta configuration and use the actual Solution ID only if this configuration genuinely requires it.

Do not randomly introduce:

featureType
solutionID
sessionInfoVersion
or other parameters.

Do not randomly change Embedded Signup version parameters.

==================================================
SESSION INFO LISTENER
==================================================

Implement ONE global listener:

window.addEventListener("message", handleEmbeddedSignupMessage)

handleEmbeddedSignupMessage(event):

1. Verify origin.
2. Safely parse event.data.
3. Ignore non-JSON messages.
4. Check:

data.type === "WA_EMBEDDED_SIGNUP"

5. Handle:

FINISH
FINISH_ONLY_WABA
ERROR

6. On FINISH:

extract:

waba_id
phone_number_id
business_id / businessId

7. Save IDs temporarily in frontend state.
8. Do NOT call backend multiple times.
9. Combine session information with the authorization code.
10. Send ONE backend request.

The listener must be registered BEFORE launching Embedded Signup.

==================================================
BACKEND API CONTRACT
==================================================

Use ONE authoritative endpoint:

POST

/api/integrations/meta/oauth/callback

Request:

{
  "code": "...",
  "redirect_uri": "https://apps.orvym.com/dashboard/integrations/",
  "waba_id": "...",
  "phone_number_id": "...",
  "business_id": "..."
}

IDs may be null only if Meta truly did not return them.

The backend must NOT silently replace missing IDs with:

/me/businesses

or another arbitrary discovery strategy.

==================================================
BACKEND FLOW
==================================================

STEP 1

Receive fresh authorization code.

Validate:

- user authenticated
- code present
- code not already processed
- request is not duplicated

STEP 2

Exchange code exactly once.

Use:

GET /v26.0/oauth/access_token

with:

client_id
client_secret
code
redirect_uri

STEP 3

Validate returned access token.

Do not expose access token to frontend.

Do not log full access token.

STEP 4

Use WABA ID and phone_number_id returned from Embedded Signup session.

STEP 5

Validate the WABA/phone number against Meta using the newly obtained integration token.

STEP 6

Fetch required phone number metadata.

STEP 7

Register the phone number if onboarding configuration requires registration.

STEP 8

Subscribe the WABA/app to required webhooks if required by the integration.

STEP 9

Persist:

user_id
business_id
waba_id
phone_number_id
display_phone_number
business_name
access_token (encrypted at rest)
token metadata
connection status
created_at
updated_at

STEP 10

Return:

{
  "success": true,
  "status": "connected",
  "waba_id": "...",
  "phone_number_id": "...",
  "business_id": "..."
}

NEVER return the raw access token to the browser.

==================================================
PERMISSIONS
==================================================

Current requested permissions:

whatsapp_business_messaging
whatsapp_business_management
public_profile

The previous /me/businesses implementation failed because it required business-portfolio access.

If the final implementation genuinely requires direct Business Portfolio API access, explicitly verify whether:

business_management

is required and configure it appropriately.

DO NOT request business_management merely to compensate for broken WABA discovery.

Prefer Embedded Signup session data + WABA-specific APIs whenever sufficient.

Before changing permissions, inspect the actual returned access token using Meta's token debugging/permission information.

Log only:

granted scopes
missing scopes
token type
app ID

Never log the token itself.

==================================================
TOKEN VALIDATION
==================================================

After token exchange, validate/debug the token.

Verify:

app_id == 3862862217342382

Verify the required WhatsApp permissions.

Do NOT assume granular_scopes always contain the same representation.

Inspect both:

scopes

and:

granular_scopes

when available.

Do not reject a valid token merely because a permission appears under a different token-scope representation.

==================================================
ERROR HANDLING
==================================================

Create explicit errors:

OAUTH_CODE_ALREADY_PROCESSED
OAUTH_CODE_EXPIRED
OAUTH_REDIRECT_URI_MISMATCH
META_PERMISSION_MISSING
WABA_NOT_RETURNED
PHONE_NUMBER_NOT_RETURNED
WABA_ACCESS_DENIED
PHONE_REGISTRATION_FAILED
WEBHOOK_SUBSCRIPTION_FAILED

For 36008:

DO NOT retry the same code.

Return:

"OAuth authorization code is invalid or was issued for a different redirect URI. Please restart WhatsApp Embedded Signup."

Frontend must then require a NEW Meta authorization flow.

==================================================
DATABASE SAFETY
==================================================

Add an idempotency mechanism.

Store a hash/fingerprint of processed authorization codes.

If the same code reaches the backend again:

DO NOT exchange it again.

Return a controlled duplicate-request response.

Never store the raw authorization code permanently.

==================================================
NO FALLBACK CHAOS
==================================================

Search the entire repository for:

FB.login
config_id
oauth/access_token
redirect_uri
/meta/oauth/callback
/me/businesses
setTimeout
exchangeable code
WA_EMBEDDED_SIGNUP
sessionInfoVersion

There must be ONE production Embedded Signup implementation.

Delete or disable obsolete OAuth implementations.

Do not leave multiple callback handlers active.

Do not leave multiple API exchange functions.

Do not leave retry loops.

==================================================
META DASHBOARD VERIFICATION
==================================================

Verify exact production configuration:

Meta App:
3862862217342382

Facebook Login for Business:
enabled/configured

Embedded Signup configuration:
2432311603846818

Production domain:
apps.orvym.com

Canonical redirect URI:
https://apps.orvym.com/dashboard/integrations/

Verify the exact URI in Meta's:

Valid OAuth Redirect URIs

and any relevant Facebook Login for Business configuration.

Verify:

Allowed Domains
contains:

apps.orvym.com

Verify the required Login/SDK settings for the current Meta configuration.

Do not add random redirect URIs.

==================================================
APP REVIEW REQUIREMENT
==================================================

The final implementation must be WORKING before the App Review screencast is recorded.

The screencast should demonstrate:

1. ORVYM login
2. Dashboard
3. Integrations
4. Click "Connect WhatsApp"
5. Meta Embedded Signup opens
6. Customer selects/creates Business Portfolio
7. Customer selects/creates WABA
8. Customer selects/registers phone number
9. Meta authorization completes
10. ORVYM receives successful callback
11. Backend token exchange succeeds
12. WABA ID is received
13. Phone Number ID is received
14. WhatsApp connection is saved
15. Dashboard shows CONNECTED
16. Send/receive a test WhatsApp message if available

DO NOT record a broken flow.

==================================================
PRODUCTION ACCEPTANCE TEST
==================================================

The implementation is NOT considered finished if only the popup opens.

It is finished ONLY when:

[ ] Meta Embedded Signup opens
[ ] User completes onboarding
[ ] Fresh authorization code received
[ ] Code exchanged exactly once
[ ] HTTP 200 token exchange
[ ] No error 36008
[ ] WA_EMBEDDED_SIGNUP session event received
[ ] WABA ID obtained
[ ] Phone Number ID obtained
[ ] Correct customer business association
[ ] Correct WhatsApp permissions
[ ] Phone number validated/registered as required
[ ] WABA webhook subscription completed
[ ] Database record created
[ ] Dashboard says CONNECTED
[ ] Test message works
[ ] Duplicate callback is rejected safely
[ ] Expired code produces controlled error
[ ] No retry loop
[ ] No /me/businesses dependency unless explicitly proven necessary
[ ] No access token exposed to frontend
[ ] No secrets exposed in logs

==================================================
MOST IMPORTANT
==================================================

DO NOT tell me:

"the code has been updated"

without testing.

After implementation:

1. Build frontend.
2. Build backend.
3. Deploy frontend.
4. Deploy backend.
5. Open production:

https://apps.orvym.com/dashboard/integrations/

6. Perform a COMPLETELY FRESH Embedded Signup.
7. Inspect browser logs.
8. Inspect Render logs.
9. Confirm exactly ONE callback request.
10. Confirm token exchange HTTP 200.
11. Confirm WA_EMBEDDED_SIGNUP session event.
12. Confirm WABA ID.
13. Confirm phone_number_id.
14. Confirm database connection.
15. Confirm dashboard connection status.
16. Test WhatsApp messaging.
17. Test duplicate callback protection.
18. Test expired-code handling.

Only then report completion.

If ANY step fails, diagnose the exact failed step and fix it before declaring the integration complete.

Do not solve one error by introducing another OAuth implementation.

This is a production stabilization/rebuild task, NOT another temporary patch.