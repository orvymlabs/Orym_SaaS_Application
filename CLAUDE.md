FINAL TASK — FIX ONLY THE REMAINING WHATSAPP EMBEDDED SIGNUP ISSUE
DO NOT BREAK THE PARTS THAT ARE ALREADY WORKING

We have already spent significant time implementing Meta WhatsApp Embedded Signup.

IMPORTANT:
The existing Embedded Signup implementation is PARTIALLY WORKING.

DO NOT REBUILD IT FROM SCRATCH.

DO NOT replace the current implementation with another OAuth flow.

DO NOT break or modify the parts that are already working.

CURRENT WORKING PARTS — PRESERVE THESE

The following parts are already working and MUST remain working:

1. Facebook SDK initializes successfully.

Current log:
[EmbeddedSignup] Message listener registered
Facebook SDK initialized with App ID: 3862862217342382

2. Official Meta Embedded Signup popup launches successfully.

Current log:
[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)

3. Correct Config ID is being used:

Config ID:
2432311603846818

4. FB.login is successfully being called with:

response_type: code
override_default_response_type: true

and:

extras: {
  setup: {},
  sessionInfoVersion: 3
}

5. Meta successfully sends an exchangeable OAuth code.

Current log:

[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

6. The browser is successfully receiving the Meta popup message.

Current log:

[EmbeddedSignup] WINDOW MESSAGE RECEIVED
origin: https://oauth.facebook.com

7. The implementation is successfully detecting the OAuth code from the Meta redirect message.

Current log:

[EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)

Therefore:

DO NOT CHANGE OR BREAK:

- Facebook SDK initialization
- FB.login()
- Config ID
- OAuth code reception
- current working popup launch
- current message listener registration
- current production URL
- existing Meta authentication flow

These parts are already working.

==================================================
THE ONLY REMAINING PROBLEM
==================================================

After receiving the OAuth code, the application gets stuck here:

[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)

Then:

[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

But:

WA_EMBEDDED_SIGNUP FINISH

never arrives.

As a result:

waba_id = missing
phone_number_id = missing

and the backend onboarding cannot continue.

The current issue is therefore AFTER OAuth code reception.

DO NOT GO BACK AND BREAK THE WORKING OAuth CODE FLOW.

==================================================
LATEST BROWSER LOGS
==================================================

Use these logs as the current baseline:

[EmbeddedSignup] Message listener registered

Facebook SDK initialized with App ID: 3862862217342382

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)

Config ID: 2432311603846818

response_type: code
override_default_response_type: true
extras: {"setup":{},"sessionInfoVersion":3}

[EmbeddedSignup] WINDOW MESSAGE RECEIVED

origin:
https://oauth.facebook.com

dataType:
string

rawData:
cb=...
domain=apps.orvym.com
is_canvas=false
origin=https%3A%2F%2Fapps.orvym.com/...
relation=opener
frame=...
code=AQK...

[EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)

[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)

[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

Then nothing else happens.

==================================================
YOUR PRIMARY TASK
==================================================

DO NOT FIX THE ALREADY WORKING PART.

ONLY FIX THE MISSING SESSION INFORMATION / FINISH EVENT HANDLING.

Determine why the current implementation is not receiving or correctly processing the:

WA_EMBEDDED_SIGNUP

session event.

The final flow must be:

Meta Embedded Signup popup
        ↓
OAuth code received
        ↓
WA_EMBEDDED_SIGNUP session event received
        ↓
FINISH event
        ↓
WABA ID received
        ↓
Phone Number ID received
        ↓
Backend callback
        ↓
Business token exchange
        ↓
WABA subscription
        ↓
Phone registration
        ↓
Database save
        ↓
WhatsApp Connected

==================================================
IMPORTANT — DO NOT ASSUME THE CURRENT CODE IS WRONG
==================================================

First inspect the existing implementation.

Do not blindly rewrite the listener.

Determine exactly why:

OAuth code is received successfully

BUT

WA_EMBEDDED_SIGNUP session data is not reaching the application.

Possible causes to investigate:

1. Incorrect session logging implementation.
2. Incorrect event listener.
3. Incorrect message parsing.
4. Incorrect origin handling.
5. Incorrect sessionInfoVersion.
6. Incorrect Embedded Signup configuration/version.
7. Config ID configuration issue.
8. Meta Embedded Signup version mismatch.
9. The session message is being received but rejected by the frontend.
10. The session message format is not being parsed correctly.
11. The popup flow is ending before FINISH.
12. The current Meta configuration does not expose the expected session information.

DO NOT GUESS.

Inspect the actual implementation and determine which one is happening.

==================================================
META MESSAGE HANDLING
==================================================

The current application already receives:

origin:
https://oauth.facebook.com

and a raw string containing:

cb=...
domain=apps.orvym.com
...
code=...

This message is correctly being detected for OAuth code reception.

DO NOT remove this behavior.

The application must ALSO correctly listen for the Embedded Signup session event.

Properly handle:

WA_EMBEDDED_SIGNUP

and the relevant events:

FINISH
CANCEL
ERROR

Do not assume all Meta messages are JSON.

Do not discard a useful Meta session message simply because it is not JSON.

However, do NOT blindly accept arbitrary window messages.

Validate the message origin and parse the expected Meta Embedded Signup message format safely.

==================================================
CODE + SESSION DATA CAN ARRIVE IN DIFFERENT ORDERS
==================================================

The implementation MUST support both cases.

CASE 1:

OAuth code arrives first:

code
↓
wait for session information
↓
FINISH
↓
WABA ID + Phone Number ID
↓
continue

CASE 2:

Session information arrives first:

WA_EMBEDDED_SIGNUP
↓
FINISH
↓
WABA ID + Phone Number ID
↓
wait for OAuth code
↓
continue

The application must continue as soon as it has:

code
+
waba_id
+
phone_number_id

Do NOT require these values to arrive in the same event.

==================================================
IMPORTANT — DO NOT EXCHANGE THE CODE EARLY
==================================================

The OAuth code is:

- single-use
- short-lived
- approximately 30 seconds

The current implementation previously attempted exchanges at the wrong stage.

Do not exchange the code multiple times.

Create one guarded completion function.

Only call the backend ONCE when all required values are available:

code
waba_id
phone_number_id

Example logical condition:

if (
  code &&
  wabaId &&
  phoneNumberId &&
  !exchangeStarted
) {
   exchangeStarted = true;
   continueOnboarding();
}

Do not create multiple timers that can exchange the same code.

==================================================
CURRENT BACKEND FLOW
==================================================

The backend endpoint is:

POST
/api/integrations/meta/oauth/callback

Production backend:

https://orym-saas-application.onrender.com

The backend should receive:

code
waba_id
phone_number_id
business_id (optional)

Once the required IDs are received, continue with the existing backend onboarding implementation.

DO NOT rewrite the backend unnecessarily.

==================================================
META TOKEN EXCHANGE
==================================================

The token exchange is ALREADY WORKING in the existing implementation.

Previously we confirmed:

META OAUTH TOKEN EXCHANGE

Meta endpoint:

https://graph.facebook.com/v26.0/oauth/access_token

Response:

Status Code: 200

Access token received: YES

Token exchange successful.

Therefore:

DO NOT break the existing successful token exchange.

Do NOT introduce the previous redirect_uri problem again.

For the current FB.login Config ID flow, follow the exact Meta flow currently being used and do not arbitrarily add/remove redirect_uri.

==================================================
PREVIOUS ERROR — DO NOT REINTRODUCE
==================================================

Previously we had:

Error code: 100
Error subcode: 36008

Error validating verification code.

This happened because the redirect_uri behavior did not match the OAuth code binding.

That problem must NOT return.

Do not make unnecessary redirect_uri changes.

==================================================
PREVIOUS MISSING PERMISSION ERROR
==================================================

Previously the backend attempted:

/me/businesses

and received:

(#100) Missing Permission

Do NOT make /me/businesses the primary WABA discovery mechanism.

Once Embedded Signup supplies:

waba_id
phone_number_id

use those IDs directly.

Do not depend on unnecessary business portfolio discovery.

==================================================
BACKEND ONBOARDING AFTER IDs ARE RECEIVED
==================================================

After the business token is successfully obtained:

STEP 1

Use the business token.

STEP 2

Subscribe the customer's WABA:

POST

/{WABA_ID}/subscribed_apps

using:

Authorization:
Bearer BUSINESS_TOKEN

STEP 3

Register the customer's phone number:

POST

/{PHONE_NUMBER_ID}/register

using:

Authorization:
Bearer BUSINESS_TOKEN

Use the application's existing registration/PIN strategy.

STEP 4

Save the successful integration in the existing database.

Store/update:

user_id
business_id
waba_id
phone_number_id
business token / encrypted token according to existing architecture
connection status
timestamps

Do not create duplicate integrations.

==================================================
VERY IMPORTANT — PRESERVE EVERYTHING ELSE
==================================================

This is an existing production SaaS.

DO NOT break:

- Login
- Signup
- Dashboard
- User authentication
- Existing WhatsApp messaging
- Existing WhatsApp webhooks
- Existing conversations
- Existing inbox
- Existing bots
- Existing automation
- Existing integrations
- Existing database records
- Existing API endpoints
- Existing UI
- Existing subscription logic
- Existing notifications
- Existing analytics

Do NOT rewrite unrelated files.

Do NOT change unrelated APIs.

Do NOT change database schema unless absolutely necessary.

Do NOT delete data.

Do NOT reset the database.

Do NOT remove existing integrations.

Do NOT replace the WhatsApp system.

Do NOT replace Embedded Signup with manual OAuth.

Make the smallest targeted change possible.

If a shared function needs modification, preserve all existing behavior for its other callers.

==================================================
META VERSION CHECK
==================================================

The current Meta documentation states that Embedded Signup v2 will be deprecated on October 15, 2026.

Therefore inspect the current Config ID:

2432311603846818

Determine which Embedded Signup version/configuration it uses.

If the current Config ID is valid and compatible with the existing implementation, DO NOT replace it unnecessarily.

If it is an outdated/deprecated configuration and that is the actual reason session information is not being delivered, explain this clearly and migrate only the Embedded Signup configuration/implementation required for the current supported Meta version.

Do not migrate blindly.

==================================================
META DASHBOARD
==================================================

Verify only the settings actually required for the current Embedded Signup configuration:

- App ID
- Config ID
- WhatsApp Business Messaging use case
- WhatsApp Business Management permission
- public_profile if required
- allowed domains
- OAuth redirect settings if required
- Embedded Signup configuration
- correct Embedded Signup version
- required business permissions

Do NOT randomly change Meta Dashboard settings.

If a setting is already correct, leave it unchanged.

==================================================
DEBUGGING REQUIREMENT
==================================================

Add safe diagnostics for the session event.

Do NOT log:

- App Secret
- Business Token
- Access Token
- Full OAuth code

Safe logs should show:

[EmbeddedSignup] SESSION EVENT RECEIVED
event:
FINISH/CANCEL/ERROR

sessionInfoVersion:
3

waba_id:
received/missing

phone_number_id:
received/missing

business_id:
received/missing

origin:
<validated origin>

Do not log sensitive credentials.

==================================================
TIMEOUT BEHAVIOR
==================================================

The current implementation reports:

WA_EMBEDDED_SIGNUP FINISH event never arrived

after a short timeout.

Do not use this timeout as proof that onboarding failed.

Use timeout only for diagnostics.

If the popup is still active, do not prematurely terminate the onboarding flow.

Do not show a false "Onboarding failed" message while the Meta flow is still active.

==================================================
DUPLICATE PROTECTION
==================================================

There must be exactly ONE onboarding attempt state.

Suggested states:

IDLE
POPUP_OPEN
CODE_RECEIVED
SESSION_RECEIVED
READY
EXCHANGING
SUBSCRIBING
REGISTERING
COMPLETED
CANCELLED
FAILED

The same OAuth code must NEVER be exchanged twice.

The backend must also safely reject/handle duplicate completion requests.

==================================================
ACCEPTANCE TEST
==================================================

Do NOT declare success just because the popup opens.

The fix is complete only when:

1. User opens:

https://apps.orvym.com/dashboard/integrations/

2. Clicks Connect WhatsApp.

3. Meta Embedded Signup popup opens.

4. Existing OAuth code reception continues working.

5. Browser receives:

LOGIN_CODE_RECEIVED

6. Browser receives:

WA_EMBEDDED_SIGNUP

7. Browser receives:

FINISH

8. Browser obtains:

waba_id

phone_number_id

9. Backend receives all required values.

10. Token exchange succeeds.

11. WABA subscription succeeds.

12. Phone registration succeeds.

13. Database integration is saved.

14. Frontend displays:

WhatsApp Connected

15. Refreshing the dashboard preserves the connection.

16. Existing WhatsApp messaging continues working.

17. Existing webhooks continue working.

18. Existing conversations continue working.

19. No duplicate integration is created.

20. No duplicate OAuth exchange occurs.

21. No 36008 error.

22. No unnecessary /me/businesses Missing Permission error.

23. No "FINISH event never arrived" during a successful onboarding.

==================================================
FINAL DEVELOPMENT RULE
==================================================

DO NOT START OVER.

The current implementation has already successfully reached:

Facebook SDK initialized
↓
Embedded Signup popup launched
↓
Meta flow executed
↓
OAuth message received
↓
OAuth code extracted

That progress MUST be preserved.

Your job is ONLY to fix what happens AFTER:

[EmbeddedSignup] LOGIN_CODE_RECEIVED

Specifically:

LOGIN_CODE_RECEIVED
        ↓
WA_EMBEDDED_SIGNUP session event
        ↓
FINISH
        ↓
WABA ID + Phone Number ID
        ↓
existing backend onboarding
        ↓
completed integration

Do NOT damage the working stages above.

Before making changes, inspect the current code and identify the smallest possible fix.

After making changes, provide:

1. Exact files changed.
2. Exact reason the FINISH/session event was not being captured.
3. Exact fix applied.
4. Any Meta Dashboard change required.
5. Any environment variable change required.
6. Exact production testing steps.
7. Expected browser logs.
8. Expected backend logs.
9. Confirmation that existing functionality was not modified unnecessarily.

DO NOT declare completion until the complete Embedded Signup onboarding works end-to-end.


CURRENT STATUS:
- Facebook SDK initializes successfully.
- FB.login() opens the official WhatsApp Embedded Signup popup.
- Config ID is correct and the popup flow starts.
- LOGIN_CODE_RECEIVED is successfully received.
- OAuth code length is 451.
- The current blocker is AFTER LOGIN_CODE_RECEIVED.
- WA_EMBEDDED_SIGNUP session event is NOT being received.
- Therefore waba_id and phone_number_id remain missing.
- The flow currently stops at:
  "code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs"
  and eventually:
  "WA_EMBEDDED_SIGNUP FINISH event never arrived".

IMPORTANT:
DO NOT rewrite, replace, or break the existing working Embedded Signup implementation.

PRESERVE:
- Facebook SDK initialization
- App ID
- Config ID
- FB.login()
- response_type=code
- override_default_response_type=true
- extras/sessionInfoVersion configuration
- existing popup flow
- existing OAuth code reception
- existing message listener
- existing dashboard UI
- existing backend OAuth endpoint
- existing working WhatsApp integration code

ONLY FIX:
Everything AFTER LOGIN_CODE_RECEIVED.

GOAL:
Make the official Meta WhatsApp Embedded Signup flow reliably deliver and parse the WA_EMBEDDED_SIGNUP session event and obtain:
- waba_id
- phone_number_id
- business_id where available

Then continue automatically with:
1. exchange the received code for the business token
2. use the business token to subscribe the app to the customer's WABA
3. register the customer's phone number
4. save the WABA ID, phone number ID, business ID and token/integration state securely
5. complete the connection in the dashboard
6. verify the integration with a real API/webhook test

IMPORTANT EVENT HANDLING:
- Listen for the official Meta WA_EMBEDDED_SIGNUP postMessage/session event exactly as required by the current Meta Embedded Signup documentation.
- Correctly handle the actual message format being returned by Meta.
- Do NOT assume every message is JSON.
- Parse the OAuth redirect/code message separately from the WA_EMBEDDED_SIGNUP session message.
- Validate message.origin securely.
- Do not discard valid Meta session messages merely because the raw message is not JSON.
- Support the current sessionInfoVersion being used by the implementation.
- Log the complete event type and safely parsed payload structure (never log access tokens/secrets).
- Do not use arbitrary timeout-based failure while the legitimate Embedded Signup popup/session is still active.
- Do not treat LOGIN_CODE_RECEIVED as completion.
- Do not exchange the OAuth code before the required session information is obtained unless Meta's current documentation explicitly requires the exchange earlier.
- Prevent duplicate code exchanges because the code is single-use.
- Handle popup completion, cancellation and genuine errors separately.

META DOCUMENTATION REQUIREMENT:
Use the CURRENT official Meta WhatsApp Embedded Signup documentation and the current Embedded Signup version required for this app. Do not rely on old Embedded Signup v2 behavior if the current documentation/version has changed.

Also verify whether the current Config ID is configured for the same Embedded Signup version and session logging/event behavior being implemented.

BACKEND:
Once the frontend obtains the session asset IDs, send them to:
POST /api/integrations/meta/oauth/callback

The backend must:
- accept the exact data produced by the current Meta flow
- exchange the code correctly according to the current Meta documentation
- obtain the business integration system user token
- subscribe the customer's WABA using:
  POST /<WABA_ID>/subscribed_apps
- register the customer's phone number using:
  POST /<PHONE_NUMBER_ID>/register
- persist the resulting integration
- return a clear success response to the frontend

Do not hard-code WABA ID, phone number ID or business ID.

OAUTH:
The previous error was:
Error code: 100
Error subcode: 36008
"Error validating verification code. Please make sure your redirect_uri is identical..."

Do NOT reintroduce the previous redirect_uri bug.

Use one canonical production configuration and keep frontend/backend behavior consistent:
https://apps.orvym.com/dashboard/integrations/

Do not randomly add/remove redirect_uri parameters. Follow the CURRENT Meta documentation for the exact FB.login/config_id flow being used.

SECURITY:
- Never expose APP_SECRET or access tokens in frontend code.
- Never log secrets.
- Keep token exchange server-to-server.
- Validate Meta message origins.
- Prevent replay/duplicate processing of the single-use OAuth code.

TESTING:
Do not tell me the implementation is fixed just because the popup opens.

The implementation is considered FIXED only when this complete flow succeeds:

Dashboard
→ Connect WhatsApp
→ official Meta Embedded Signup opens
→ customer completes Meta onboarding
→ WA_EMBEDDED_SIGNUP session event received
→ WABA ID received
→ phone number ID received
→ OAuth code received
→ backend token exchange succeeds
→ WABA subscribed_apps succeeds
→ phone registration succeeds
→ integration saved
→ dashboard shows WhatsApp Connected
→ webhook/message test succeeds.

After implementation, provide:
1. exact files changed
2. exact root cause
3. Meta-side configuration that was required
4. test results
5. any remaining blocker, if one exists.

DO NOT modify unrelated WhatsApp, dashboard, authentication, webhook, bot, database or UI functionality.