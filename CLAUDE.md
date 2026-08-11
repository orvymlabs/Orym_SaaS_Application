FINAL TASK — FIX META WHATSAPP EMBEDDED SIGNUP END-TO-END
WITHOUT BREAKING ANY EXISTING FUNCTIONALITY

We need to permanently fix the CURRENT production WhatsApp Embedded Signup integration in ORVYM Nexus.

IMPORTANT:
The existing system is already partially working. DO NOT rebuild the integration from scratch.

The OAuth authorization code is successfully being received from Meta.

Current production logs show:

[EmbeddedSignup] Message listener registered
Facebook SDK initialized with App ID: 3862862217342382
[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)
Config ID: 2432311603846818
response_type: code | override_default_response_type: true | extras: {"setup":{},"sessionInfoVersion":3}

Then:

[EmbeddedSignup] WINDOW MESSAGE RECEIVED
origin: https://oauth.facebook.com
dataType: string
isJSON: false
containsOAuthCode: true
containsWA_EMBEDDED_SIGNUP: false
containsSessionInfo: false
waba_id present: false
phone_number_id present: false
business_id present: false

[EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)
[EmbeddedSignup] code received, waiting briefly for WA_EMBEDDED_SIGNUP session asset IDs
[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

Then it gets stuck because:

WA_EMBEDDED_SIGNUP session event is NOT being received.

Therefore:

oauthCodeReceived = true
wabaIdReceived = false
phoneNumberIdReceived = false
businessIdReceived = false

==================================================
CRITICAL REQUIREMENT — DO NOT BREAK ANYTHING
==================================================

This is extremely important.

DO NOT break, remove, rewrite, or unnecessarily modify anything that is already working.

The following functionality MUST remain working exactly as before:

- Facebook SDK initialization
- Meta FB.login flow
- Current Embedded Signup popup
- Config ID: 2432311603846818
- OAuth authorization code generation/receipt
- Existing OAuth fallback handling
- Login/authentication
- Dashboard
- Integrations page
- Existing WhatsApp integration
- Webhooks
- Incoming WhatsApp messages
- Outgoing WhatsApp messages
- Conversations
- Notifications
- Bots
- Leads
- Analytics
- Database
- Existing API routes
- Existing frontend/backend architecture

DO NOT replace the official Meta Embedded Signup flow with another implementation.

DO NOT replace FB.login(config_id) with a custom OAuth implementation.

DO NOT randomly change the Config ID.

DO NOT remove the existing OAuth code handling because it is already working.

DO NOT make unrelated refactors.

DO NOT change unrelated files.

Make the SMALLEST SAFE TARGETED CHANGE required to fix the missing Embedded Signup session event and complete onboarding.

Before changing anything, inspect the current implementation and understand how the existing flow works.

==================================================
CURRENT ROOT PROBLEM TO INVESTIGATE
==================================================

The current launch configuration contains:

extras: {
    setup: {},
    sessionInfoVersion: 3
}

This must be investigated carefully.

For the Meta Tech Provider / Partner Solution flow, verify whether the Embedded Signup configuration requires:

extras: {
    setup: {
        solutionID: "<VALID_EXISTING_SOLUTION_ID>"
    },
    sessionInfoVersion: 3
}

IMPORTANT:

DO NOT invent a Solution ID.

First inspect:

- existing environment variables
- frontend configuration
- backend configuration
- Meta integration settings
- existing project documentation
- any existing Partner Solution / Solution ID configuration

If a valid Solution ID already exists, use that exact existing value.

If no Solution ID exists, DO NOT fabricate one.

Instead report exactly what Meta configuration is missing and where the valid Solution ID must be obtained/configured.

==================================================
META EMBEDDED SIGNUP MESSAGE HANDLING
==================================================

The current OAuth redirect message:

cb=...&domain=apps.orvym.com&...&code=...

is NOT the Embedded Signup completion event.

The frontend must NOT treat this message as:

WA_EMBEDDED_SIGNUP

It should extract/store the OAuth code and continue waiting for the actual Embedded Signup session event.

The message listener must safely handle:

window.message

and validate the origin.

It must continue listening for the actual Meta event.

Expected successful session event is equivalent to:

{
    "data": {
        "phone_number_id": "<PHONE_NUMBER_ID>",
        "waba_id": "<WABA_ID>",
        "business_id": "<BUSINESS_ID>"
    },
    "type": "WA_EMBEDDED_SIGNUP",
    "event": "FINISH",
    "version": 3
}

Extract:

- waba_id
- phone_number_id
- business_id

Do not depend on one undocumented response shape if Meta's current documented response uses a valid variant.

Handle the appropriate successful completion event such as:

FINISH

and, where applicable to the configured flow:

FINISH_ONLY_WABA

Also handle:

ERROR

and cancellation separately.

Do NOT show onboarding failure simply because the OAuth redirect message was received.

==================================================
IMPORTANT — HANDLE BOTH ARRIVAL ORDERS
==================================================

OAuth code and session information may arrive at different times.

Implement a safe pending-state mechanism:

pendingOAuthCode
pendingSessionInfo

If OAuth code arrives first:

store OAuth code
wait for session information

If session information arrives first:

store session information
wait for OAuth code

When both are available:

finalizeEmbeddedSignup()

must run exactly once.

Use an idempotency guard so the backend provisioning cannot execute twice.

Do NOT depend on a long fixed timeout as the primary solution.

The current timeout is only diagnostic/error handling.

The real trigger should be:

OAuth code available
+
session information available

==================================================
BACKEND PROVISIONING
==================================================

After both OAuth code and session information are available:

1. Send the required data to backend exactly once.

2. Exchange the one-time OAuth code server-to-server for the customer's business token.

3. APP_SECRET must remain server-side.

4. Never expose APP_SECRET or business token to frontend.

5. Never exchange the same OAuth code twice.

6. Use the returned business token.

7. Subscribe the customer's WABA:

POST /<WABA_ID>/subscribed_apps

8. Register the customer's business phone number:

POST /<PHONE_NUMBER_ID>/register

using the required WhatsApp messaging product and 6-digit PIN.

9. Save the integration against the correct authenticated user/tenant:

- WABA ID
- phone number ID
- business ID
- secure business token
- connection status
- relevant Meta identifiers

10. Return a clear success response.

11. Frontend must finally show:

WhatsApp Connected

==================================================
SECURITY
==================================================

Never log:

- APP_SECRET
- business access token
- complete OAuth code
- private credentials

Safe logs are allowed:

- OAuth code received: true
- code length
- WABA ID
- phone number ID
- business ID
- event type
- event name
- provisioning status
- Meta API status/error code

==================================================
META CONFIGURATION VERIFICATION
==================================================

Before changing application code, verify the existing Meta setup:

1. App ID
2. Config ID
3. Facebook Login for Business configuration
4. WhatsApp Embedded Signup configuration
5. Tech Provider status
6. Partner Solution / Solution ID
7. Business Verification
8. App Review / Access Verification
9. Required permissions
10. App domains
11. Production domain
12. OAuth configuration
13. JavaScript SDK domain configuration
14. WhatsApp assets
15. Webhook configuration

Production frontend:

https://apps.orvym.com

Do NOT introduce localhost URLs into production.

Do NOT change the production domain.

==================================================
VERSION REQUIREMENT
==================================================

Keep the currently working:

sessionInfoVersion: 3

Do NOT randomly downgrade or upgrade it.

Do NOT migrate to another Embedded Signup version unless the current Meta configuration explicitly requires it.

The immediate goal is to fix the CURRENT production implementation safely.

==================================================
REGRESSION PROTECTION — VERY IMPORTANT
==================================================

Before editing:

1. Inspect the current frontend Embedded Signup implementation.
2. Inspect backend Meta routes.
3. Inspect token exchange implementation.
4. Inspect webhook implementation.
5. Inspect database integration model.
6. Inspect environment variables.
7. Understand the current working flow.

Then make only the minimum changes necessary.

After implementation, verify that the following still work:

- Facebook SDK
- FB.login
- Embedded Signup popup
- OAuth code reception
- OAuth fallback handling
- authentication
- dashboard
- integrations page
- WhatsApp connection
- webhooks
- incoming messages
- outgoing messages
- conversations
- notifications
- bots
- leads
- analytics
- database
- existing API routes

If any existing behavior is already working, PRESERVE IT.

Do not "clean up" or refactor unrelated code while fixing this issue.

==================================================
PRODUCTION TEST
==================================================

Test the complete flow from a fresh browser/session:

1. Open production app.
2. Login.
3. Open Integrations.
4. Start WhatsApp Embedded Signup.
5. Complete Meta onboarding.
6. Confirm OAuth code is received.
7. Confirm WA_EMBEDDED_SIGNUP event is received.
8. Confirm WABA ID is received.
9. Confirm phone number ID is received.
10. Confirm business ID where applicable.
11. Confirm backend receives the data.
12. Confirm token exchange succeeds.
13. Confirm WABA subscribed_apps succeeds.
14. Confirm phone registration succeeds.
15. Confirm integration is saved.
16. Confirm UI shows WhatsApp Connected.
17. Send test WhatsApp message.
18. Receive test WhatsApp message.
19. Confirm webhook delivery.
20. Confirm conversation appears in dashboard.

Also test:

- fresh browser
- existing Meta login session
- another Chrome profile/incognito
- cancellation
- Meta error
- already-connected account

==================================================
SUCCESS CRITERIA
==================================================

DO NOT declare the issue fixed merely because:

"OAuth code received"

That is NOT complete success.

The complete success chain is:

OAuth code received
        ↓
WA_EMBEDDED_SIGNUP event received
        ↓
WABA ID received
        ↓
Phone Number ID received
        ↓
Business ID received where applicable
        ↓
Backend receives session data
        ↓
Business token exchange succeeds
        ↓
WABA subscribed_apps succeeds
        ↓
Phone number registration succeeds
        ↓
Integration saved in database
        ↓
UI shows WhatsApp Connected
        ↓
Incoming message works
        ↓
Outgoing message works

==================================================
FINAL REPORT REQUIRED
==================================================

After making the fix, provide:

1. Exact root cause.
2. Exact files changed.
3. Exact configuration/environment variables required.
4. Whether Solution ID was missing, incorrect, or already correct.
5. What was changed in Embedded Signup launch configuration.
6. What was changed in message listener.
7. What was changed in backend provisioning.
8. Test results.
9. Confirmation that OAuth code reception remains working.
10. Confirmation that existing Embedded Signup functionality was NOT unnecessarily rewritten.
11. Confirmation that unrelated system functionality was NOT modified.
12. Any remaining Meta-side requirement, if one exists.

MOST IMPORTANT:

FIX THE CURRENT ISSUE, BUT PRESERVE EVERYTHING THAT IS ALREADY WORKING.

Do not rewrite the entire Meta integration.

Do not break the existing Embedded Signup.

Do not break OAuth.

Do not break webhooks.

Do not break WhatsApp messaging.

Do not break the dashboard.

Do not modify unrelated functionality.

Use the smallest, safest, production-ready fix and verify the complete onboarding flow end-to-end.