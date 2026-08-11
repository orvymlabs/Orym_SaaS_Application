THE CURRENT LOGS CONFIRM THE EXACT FAILURE POINT.

DO NOT CHANGE OR REBUILD THE EXISTING META EMBEDDED SIGNUP POPUP.

The following parts are WORKING and MUST REMAIN UNCHANGED:

- Facebook SDK initialization
- App ID: 3862862217342382
- Config ID: 2432311603846818
- FB.login()
- Embedded Signup popup
- OAuth code reception
- current Meta login flow

CURRENT SUCCESS:

[EmbeddedSignup] Message listener registered
Facebook SDK initialized
Launching WhatsApp Embedded Signup
Config ID: 2432311603846818
response_type: code
override_default_response_type: true
sessionInfoVersion: 3

Then Meta sends:

origin: https://oauth.facebook.com

The application successfully extracts:

LOGIN_CODE_RECEIVED (length: 451)

Therefore DO NOT TOUCH THE EXISTING OAUTH CODE RECEPTION.

==================================================
CURRENT BUG
==================================================

After LOGIN_CODE_RECEIVED, the application waits for:

WA_EMBEDDED_SIGNUP session event

but this event is NEVER received.

Current diagnostics:

messages_received:
[
  {
    origin: "https://oauth.facebook.com",
    type: "non-json-string"
  }
]

saw_WA_EMBEDDED_SIGNUP_event: false
saw_CANCEL: false
saw_ERROR: false

oauthCodeReceived: true
wabaIdReceived: false
phoneNumberIdReceived: false
businessIdReceived: false

The application currently waits 5 MINUTES and then fails.

This timeout is NOT the solution.

DO NOT increase the timeout again.

==================================================
ROOT CAUSE TO INVESTIGATE
==================================================

The current implementation is receiving the OAuth redirect message, but it is NOT receiving/recognizing the WhatsApp Embedded Signup session information.

The current code appears to be treating the OAuth redirect message as the important message and then waiting for another WA_EMBEDDED_SIGNUP message which never arrives.

Inspect the actual Meta Embedded Signup implementation and determine WHY the expected session information is not being delivered/recognized.

Do NOT assume that simply increasing the timeout will solve this.

==================================================
CRITICAL: VERIFY META'S ACTUAL SESSION LOGGING IMPLEMENTATION
==================================================

Inspect the current implementation against Meta's CURRENT Embedded Signup documentation.

Verify the exact required implementation for:

sessionInfoVersion
WA_EMBEDDED_SIGNUP
postMessage
message event listener
session logging
waba_id
phone_number_id
business_id

Do not invent an event format.

Do not assume the event is JSON if Meta sends a different documented format.

Do not discard a message merely because it is a string.

Do not treat every message from oauth.facebook.com as an OAuth redirect.

The implementation must correctly distinguish:

1. OAuth/login-code message
2. Embedded Signup session logging message
3. Embedded Signup FINISH event
4. CANCEL event
5. ERROR event
6. unrelated Meta messages

==================================================
IMPORTANT: INSPECT THE RAW MESSAGE
==================================================

The current log shows:

dataType: string

rawData contains:

cb=...
domain=apps.orvym.com
is_canvas=false
origin=https://apps.orvym.com/...
relation=opener
frame=...
code=...

This appears to be the OAuth redirect-style message.

Do NOT assume this is the WA_EMBEDDED_SIGNUP session event.

Instrument the listener to safely identify EVERY message received during the Embedded Signup attempt.

For each message log ONLY safe metadata:

- event origin
- typeof event.data
- whether it is JSON
- whether it contains an OAuth code
- whether it contains WA_EMBEDDED_SIGNUP
- whether it contains session information
- whether WABA ID exists
- whether phone number ID exists
- whether business ID exists

Never log:
- full OAuth code
- access tokens
- business tokens
- app secret
- passwords

==================================================
VERY IMPORTANT: VERIFY sessionInfoVersion=3
==================================================

The current implementation sends:

extras: {
    setup: {},
    sessionInfoVersion: 3
}

Verify that this is actually supported by the CURRENT Meta Embedded Signup configuration represented by Config ID:

2432311603846818

Do NOT blindly keep or remove sessionInfoVersion.

Determine from the current Meta documentation and actual Config ID configuration whether:

sessionInfoVersion: 3

is correct for this Embedded Signup configuration.

If the Config ID is configured for a different session logging/version behavior, fix the mismatch.

Do NOT create a new Config ID unless absolutely necessary.

==================================================
CHECK THE META CONFIGURATION
==================================================

Inspect the Meta Embedded Signup configuration associated with:

Config ID:
2432311603846818

Verify:

- Embedded Signup version
- session logging configuration
- sessionInfoVersion compatibility
- allowed domains
- WhatsApp Business setup
- required permissions
- Tech Provider / Solution Provider configuration
- whether the Config ID is configured to return session information

Do NOT randomly change permissions.

Do NOT remove existing permissions.

Do NOT modify unrelated Meta settings.

If a Meta Dashboard change is required, clearly state exactly what needs to be changed BEFORE changing it.

==================================================
DO NOT DEPEND ONLY ON THE FINISH EVENT
==================================================

The application currently behaves like:

LOGIN_CODE_RECEIVED
↓
WAIT FOR WA_EMBEDDED_SIGNUP FINISH
↓
if FINISH does not arrive
↓
wait 5 minutes
↓
FAIL

This is wrong.

The implementation must process the documented session information as soon as it becomes available.

Do not require a specific FINISH event if Meta's current documented flow provides the required asset information through another supported mechanism.

==================================================
SERVER-SIDE FALLBACK
==================================================

Do not make the browser's WA_EMBEDDED_SIGNUP event the ONLY way to obtain:

waba_id
phone_number_id

After receiving the exchangeable OAuth code, use the documented server-side onboarding process.

Backend endpoint:

POST /api/integrations/meta/oauth/callback

The backend must:

1. Receive the single-use OAuth code.
2. Exchange it server-to-server with Meta.
3. Obtain the business token.
4. Resolve the customer's WABA using the documented Meta API.
5. Resolve the customer's phone number ID using the documented Meta API.
6. Subscribe the WABA to the app.
7. Register the phone number if required.
8. Save the integration for the authenticated user/tenant.
9. Return success.

Do NOT fabricate any ID.

Do NOT use:
- App ID as WABA ID
- business ID as WABA ID
- WhatsApp phone number as phone_number_id
- hardcoded IDs
- stale cached IDs

==================================================
IMPORTANT ABOUT THE OAUTH CODE
==================================================

The OAuth code is single-use.

Once LOGIN_CODE_RECEIVED happens:

- store it once
- prevent duplicate exchange
- do not exchange it repeatedly while waiting for frontend session events
- do not call the backend multiple times with the same code

Use an attempt ID / ref / server-side idempotency guard if necessary.

==================================================
DO NOT BREAK CURRENT EMBEDDED SIGNUP
==================================================

ABSOLUTE REQUIREMENT:

The following MUST continue working exactly as it currently does:

FB.login()
→ Meta popup
→ customer onboarding
→ OAuth code returned
→ LOGIN_CODE_RECEIVED

Do not rewrite this section.

Do not replace it with:
- normal Facebook OAuth
- another login flow
- custom popup
- redirect-based OAuth
- a different Meta SDK
- another Config ID

Only fix the post-code onboarding stage.

==================================================
REMOVE THE FALSE 5-MINUTE FAILURE
==================================================

Do NOT simply change:

5 minutes → 10 minutes

That is NOT a fix.

The system must either:

A) correctly receive the documented Embedded Signup session information

OR

B) use the documented server-side fallback to resolve the customer's WhatsApp assets after the OAuth code is exchanged.

The user should not sit on an onboarding screen for five minutes waiting for an event that is not being delivered.

==================================================
TESTING
==================================================

After the fix test:

1. Existing Meta Embedded Signup popup opens.
2. OAuth code is received.
3. No duplicate OAuth exchange occurs.
4. WABA ID is resolved.
5. phone_number_id is resolved.
6. Business ID is resolved if required.
7. Backend receives the onboarding request.
8. Business token is obtained.
9. WABA subscription succeeds.
10. Phone registration succeeds if required.
11. Integration is saved.
12. Dashboard shows WhatsApp Connected.

Also verify that these existing systems still work:

- Login
- Dashboard
- Bots
- Conversations
- Notifications
- Analytics
- Existing integrations
- WhatsApp webhooks

==================================================
DO NOT CHANGE UNRELATED CODE
==================================================

Make the smallest possible targeted fix.

Before modifying anything, identify:

- current frontend Embedded Signup file
- current message listener
- current OAuth-code extraction
- current WA_EMBEDDED_SIGNUP parsing
- current timeout
- current backend OAuth callback
- current Meta Graph API onboarding logic

Then modify only what is necessary.

==================================================
FINAL REPORT REQUIRED
==================================================

After fixing, report:

1. Exact root cause.
2. Why OAuth code was received but WA_EMBEDDED_SIGNUP was not.
3. Whether sessionInfoVersion=3 is correct.
4. Whether Config ID 2432311603846818 is correctly configured.
5. Exact frontend files changed.
6. Exact backend files changed.
7. How WABA ID is resolved.
8. How phone_number_id is resolved.
9. How duplicate OAuth exchange is prevented.
10. Whether any Meta Dashboard change was required.
11. Confirmation that FB.login() and the existing Embedded Signup popup were NOT replaced.
12. Confirmation that no unrelated functionality was changed.
13. Complete end-to-end test result.

SUCCESS CRITERIA:

The flow must reach:

LOGIN_CODE_RECEIVED
↓
WABA ID resolved
↓
Phone Number ID resolved
↓
Business token obtained
↓
WABA subscribed
↓
Phone registered if required
↓
Integration saved
↓
WhatsApp Connected

Do NOT consider the task complete just because the OAuth code is received.

The task is complete only when the actual WhatsApp Business integration is successfully onboarded.