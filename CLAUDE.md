FINAL PRODUCTION FIX — WHATSAPP EMBEDDED SIGNUP

This is the FINAL attempt to make our WhatsApp Embedded Signup work end-to-end.

DO NOT make random OAuth/redirect changes.
DO NOT replace the Embedded Signup flow with normal OAuth.
DO NOT hardcode WABA IDs or phone number IDs.
DO NOT use /me/businesses as the primary way to discover the customer's WABA.

CURRENT PRODUCTION APP:

Frontend:
https://apps.orvym.com

Dashboard:
https://apps.orvym.com/dashboard/integrations/

Backend:
https://orym-saas-application.onrender.com

Meta App ID:
3862862217342382

Embedded Signup Config ID:
2432311603846818

CURRENT PRODUCTION LOG:

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)
[EmbeddedSignup] Config ID: 2432311603846818
[EmbeddedSignup] response_type: code
[EmbeddedSignup] override_default_response_type: true
[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)
[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs
[EmbeddedSignup] WA_EMBEDDED_SIGNUP FINISH event never arrived - showing onboarding error

This means:

1. Facebook SDK initializes successfully.
2. Embedded Signup launches successfully.
3. Meta returns the exchangeable authorization code successfully.
4. The current blocker is that the frontend is NOT receiving/capturing the WA_EMBEDDED_SIGNUP session message containing the onboarding result.

FIX THE ACTUAL ROOT CAUSE.

==================================================
PART 1 — IMPLEMENT THE SESSION MESSAGE LISTENER CORRECTLY
==================================================

The WA_EMBEDDED_SIGNUP listener MUST be registered BEFORE FB.login() is called.

Do not register it after FB.login.
Do not register it conditionally after the code callback.
Do not register multiple copies of the listener.

Use one stable listener for the entire signup attempt.

The listener must inspect window message events and safely parse event.data.

It must support:

event.type === "WA_EMBEDDED_SIGNUP"

Successful completion:

event === "FINISH"

Also support:

event === "FINISH_ONLY_WABA"

and other legitimate Embedded Signup finish variants relevant to the configured flow.

Also handle:

event === "CANCEL"
event === "ERROR"

Do NOT assume only FINISH exists.

==================================================
PART 2 — DO NOT REJECT THE FACEBOOK ORIGIN INCORRECTLY
==================================================

The current code may be silently rejecting the Meta message because of an incorrect event.origin check.

Implement safe Facebook-origin validation.

Accept the legitimate Facebook origins used by the SDK/Embedded Signup flow.

At minimum handle the actual production origin:

https://www.facebook.com

and any legitimate facebook.com subdomain required by the SDK.

Do NOT blindly accept arbitrary origins.

Log rejected origins during debugging:

[EmbeddedSignup] Ignored message origin: <origin>

This is extremely important.

==================================================
PART 3 — LOG EVERY MESSAGE DURING EMBEDDED SIGNUP
==================================================

For debugging, while an Embedded Signup attempt is active, log every window message event in a safe way.

Example:

[EmbeddedSignup] WINDOW MESSAGE RECEIVED
origin: <origin>
dataType: <typeof event.data>
rawData: <safe/truncated data>

If event.data is JSON, parse it and log:

[EmbeddedSignup] PARSED MESSAGE
type:
event:
version:
data keys:

If event.data contains OAuth code/token/secrets, NEVER print the actual secret.

Redact sensitive values.

We need to know exactly whether Meta is:

A. sending WA_EMBEDDED_SIGNUP but our listener misses it
B. sending a different event name
C. sending it from an origin our code rejects
D. sending an event with an unexpected version
E. not sending the session event because the Meta configuration is incorrect

DO NOT GUESS.

==================================================
PART 4 — USE THE CORRECT SESSION INFO CONFIGURATION
==================================================

The FB.login configuration must explicitly request session information.

Keep:

config_id: "2432311603846818"
response_type: "code"
override_default_response_type: true

Use the correct Embedded Signup extras structure for our current Meta configuration.

The session information version must be explicitly configured.

Use:

sessionInfoVersion: 3

unless the existing Meta configuration explicitly requires another supported version.

Do NOT randomly switch between version 2 and version 3.

Make sure the value is passed inside the actual FB.login extras object used in production.

==================================================
PART 5 — DO NOT USE LOGIN_CODE_RECEIVED AS COMPLETION
==================================================

This is critical.

The following:

response.authResponse.code

is only the exchangeable authorization code.

It is NOT proof that Embedded Signup finished.

When LOGIN_CODE_RECEIVED occurs:

store the code temporarily.

Then wait for:

WA_EMBEDDED_SIGNUP

completion event.

When the session event arrives, capture:

waba_id
phone_number_id
business_id

where provided.

Expected successful structure is conceptually:

{
  type: "WA_EMBEDDED_SIGNUP",
  event: "FINISH",
  version: 3,
  data: {
    waba_id: "...",
    phone_number_id: "...",
    business_id: "..."
  }
}

Do not require business_id if Meta does not return it in this flow.

==================================================
PART 6 — HANDLE FINISH_ONLY_WABA
==================================================

If the flow produces:

event === "FINISH_ONLY_WABA"

do not treat this as an error.

Capture:

waba_id

and understand that phone_number_id may legitimately be unavailable in this completion mode.

Do NOT force phone_number_id when the selected flow intentionally only shares the WABA.

However, because our product needs a WhatsApp phone number for messaging, the backend should then continue with the correct phone-number setup/registration step rather than silently failing.

==================================================
PART 7 — HANDLE OTHER FINISH STATES
==================================================

Support legitimate completion events such as:

FINISH
FINISH_ONLY_WABA
FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING
FINISH_OBO_MIGRATION
FINISH_GRANT_ONLY_API_ACCESS

Only process the states that are applicable to our configured use case.

For unsupported states, log:

[EmbeddedSignup] Unsupported completion event: <event>

Do not silently treat every non-FINISH event as CANCEL.

==================================================
PART 8 — HANDLE CANCEL AND ERROR
==================================================

If:

event === "CANCEL"

log:

[EmbeddedSignup] User cancelled Embedded Signup
current_step: ...

Do not call the backend.

If:

event === "ERROR"

log:

[EmbeddedSignup] Meta Embedded Signup ERROR
error_message:
error_code:
current_step:

Do not attempt token exchange with an incomplete flow.

==================================================
PART 9 — CORRECT STATE MANAGEMENT
==================================================

Create a single signup attempt state:

{
  code: null,
  waba_id: null,
  phone_number_id: null,
  business_id: null,
  completion_event: null,
  backend_called: false
}

The code and WA_EMBEDDED_SIGNUP event can arrive in either order.

Therefore the implementation must support BOTH:

CASE A:

code arrives first
→ wait for session event
→ receive WABA/phone IDs
→ exchange

CASE B:

session event arrives first
→ store WABA/phone IDs
→ wait for code
→ exchange

Do NOT assume a fixed event order.

==================================================
PART 10 — PREVENT DUPLICATE TOKEN EXCHANGE
==================================================

The Meta authorization code is single-use and short-lived.

Therefore:

backendCalled must prevent duplicate requests.

Once the backend request starts:

backendCalled = true

Do not send the same code twice.

Do not implement repeated retries using the same authorization code.

If the exchange fails, the user must start a fresh Embedded Signup attempt.

==================================================
PART 11 — DO NOT BLOCK FOREVER WAITING FOR FINISH
==================================================

Do not immediately show:

"WA_EMBEDDED_SIGNUP FINISH event never arrived"

just because the authorization code was received.

Give the Embedded Signup flow enough time to complete.

Only trigger timeout after the popup/session has actually closed or after a reasonable timeout.

When timeout occurs, show diagnostics:

- Did we receive any WA_EMBEDDED_SIGNUP event?
- What origins were received?
- What message types were received?
- Was the popup closed?
- Did Meta send CANCEL?
- Did Meta send ERROR?

==================================================
PART 12 — IMPORTANT REACT/NEXT.JS REQUIREMENT
==================================================

This is a Next.js production application.

Make sure the message listener is not broken by React lifecycle behavior.

Do NOT accidentally:

- register listener on every render
- remove listener while popup is active
- create a stale closure
- register duplicate listeners
- lose signup state because the component rerenders

Use a stable callback/ref/state strategy.

The listener must remain alive during the entire Embedded Signup session.

Clean it up only after the signup attempt is completely finished.

==================================================
PART 13 — VERIFY FB.LOGIN CONFIGURATION
==================================================

Use exactly:

FB.login(callback, {
    config_id: "2432311603846818",
    response_type: "code",
    override_default_response_type: true,
    extras: {
        setup: {},
        sessionInfoVersion: 3
    }
})

If our Meta Embedded Signup configuration requires a solutionID or other required setup parameter, preserve the existing configured value.

DO NOT invent a new Config ID.

DO NOT create a new OAuth flow.

==================================================
PART 14 — TOKEN EXCHANGE
==================================================

The token exchange has already worked successfully in production.

Previous successful Render log:

Status Code: 200
Access token received: YES
Token exchange successful

Therefore DO NOT break the working token exchange.

Keep the existing successful exchange implementation.

Use the received authorization code exactly once.

Do not add/remove redirect_uri blindly.

The redirect URI must match the actual flow configuration if this flow requires it.

The current problem is SESSION EVENT CAPTURE, not blindly changing OAuth again.

==================================================
PART 15 — BACKEND CALLBACK
==================================================

Existing endpoint:

POST /api/integrations/meta/oauth/callback

Keep this endpoint.

When the frontend has enough information, send:

{
  "code": "<exchangeable_code>",
  "redirect_uri": "https://apps.orvym.com/dashboard/integrations/",
  "waba_id": "<waba_id>",
  "phone_number_id": "<phone_number_id>",
  "business_id": "<business_id_if_available>"
}

Do not send fake/null IDs.

If a completion event legitimately does not provide phone_number_id, handle that specific flow correctly instead of inventing one.

==================================================
PART 16 — REMOVE THE OLD /me/businesses DEPENDENCY
==================================================

The previous implementation attempted:

GET /me/businesses

and received:

(#100) Missing Permission

Do NOT use /me/businesses as the primary WABA discovery mechanism.

Once Embedded Signup returns:

waba_id
phone_number_id

use those exact customer asset IDs.

The previous Missing Permission error should not return simply because we are trying to discover the WABA through an unnecessary business edge.

==================================================
PART 17 — AFTER TOKEN EXCHANGE
==================================================

After successful token exchange:

1. Validate the WABA ID.
2. Validate/access the phone number ID when available.
3. Retrieve required WhatsApp business information.
4. Register/configure the phone number if required by the selected Embedded Signup flow.
5. Subscribe the WABA/app to the required webhook.
6. Save the integration for the authenticated application user.
7. Store required IDs securely.
8. Store the token securely.
9. Mark integration as connected only after setup succeeds.

==================================================
PART 18 — DO NOT MARK CONNECTED TOO EARLY
==================================================

The UI must show:

Connecting...

while onboarding is in progress.

Only show:

WhatsApp Connected

after backend provisioning succeeds.

If backend provisioning fails, show:

WhatsApp connection failed

with the actual safe error.

==================================================
PART 19 — META APP CONFIGURATION CHECK
==================================================

Before changing code, verify the Meta dashboard configuration for:

App ID:
3862862217342382

Config ID:
2432311603846818

Verify:

- WhatsApp Business Platform/use case is configured.
- Facebook Login for Business / Embedded Signup is configured correctly.
- The Config ID belongs to THIS Meta app.
- The production domain is allowed.
- Required OAuth redirect URI is registered exactly.
- Required permissions are configured.
- App mode/configuration is appropriate for the current test.
- Required Advanced Access/App Review requirements are completed where necessary.

DO NOT create a second Meta app or second Config ID.

==================================================
PART 20 — IMPORTANT PERMISSIONS
==================================================

The app currently requests:

whatsapp_business_messaging
whatsapp_business_management
public_profile

Verify that the required permissions are actually available to the access token produced by the Embedded Signup flow.

Do not assume that adding a permission to the App Review submission automatically grants it to the runtime token.

If a Graph API call returns:

(#100) Missing Permission

identify exactly which endpoint/permission is missing.

Do not solve permission errors by randomly adding unrelated permissions.

==================================================
PART 21 — PRODUCTION TEST
==================================================

After implementation:

DEPLOY FRONTEND.

DEPLOY BACKEND.

Open:

https://apps.orvym.com/dashboard/integrations/

Start a COMPLETELY NEW Embedded Signup attempt.

Do NOT reuse an old authorization code.

Complete the entire Meta onboarding flow.

Expected browser logs:

[EmbeddedSignup] Launching WhatsApp Embedded Signup
[EmbeddedSignup] Message listener registered
[EmbeddedSignup] LOGIN_CODE_RECEIVED
[EmbeddedSignup] WINDOW MESSAGE RECEIVED
[EmbeddedSignup] WA_EMBEDDED_SIGNUP EVENT RECEIVED
[EmbeddedSignup] event: FINISH
[EmbeddedSignup] waba_id: <ID>
[EmbeddedSignup] phone_number_id: <ID>
[EmbeddedSignup] backend request started
[EmbeddedSignup] backend response: 200
[EmbeddedSignup] WhatsApp integration connected

Expected Render logs:

[EmbeddedSignup] Step 1/5 token exchange started
[EmbeddedSignup] Token exchange successful
[EmbeddedSignup] Step 2/5 WABA validation
[EmbeddedSignup] Step 3/5 phone validation
[EmbeddedSignup] Step 4/5 webhook setup
[EmbeddedSignup] Step 5/5 integration saved
[EmbeddedSignup] SUCCESS

==================================================
PART 22 — IF FINISH STILL DOES NOT ARRIVE
==================================================

DO NOT make another random code change.

Capture the diagnostic output:

1. Every message origin received.
2. Every message type received.
3. Parsed event names.
4. sessionInfoVersion actually passed to FB.login.
5. Exact extras object used by the production build.
6. Whether the listener was registered before FB.login.
7. Whether Meta popup actually completed or was closed.
8. Whether the Meta Config ID is configured for the same App ID.
9. Whether the required permissions are granted/available.
10. Whether the app/configuration supports session information.

Then identify the exact root cause.

==================================================
FINAL ACCEPTANCE CRITERIA
==================================================

The task is NOT considered complete because the code compiles.

It is complete ONLY when a fresh production user can:

1. Click Connect WhatsApp.
2. Open official Meta Embedded Signup.
3. Complete the onboarding.
4. Generate the exchangeable code.
5. Receive WA_EMBEDDED_SIGNUP completion event.
6. Receive waba_id.
7. Receive phone_number_id when applicable.
8. Send the correct information to backend.
9. Exchange the code successfully.
10. Configure the WABA.
11. Configure/register the phone number when required.
12. Subscribe the webhook.
13. Save the integration to the correct user.
14. Return to the dashboard.
15. See WhatsApp Connected.
16. Send/receive a real WhatsApp test message.

NO MORE PLACEHOLDERS.
NO HARD-CODED CUSTOMER ASSET IDs.
NO RANDOM REDIRECT URI CHANGES.
NO /me/businesses DEPENDENCY FOR WABA DISCOVERY.
NO DUPLICATE CODE EXCHANGE.
NO SILENT EVENT DROPPING.

MOST IMPORTANT:
Before telling me it is fixed, perform a real production Embedded Signup test and provide the exact browser + Render log sequence proving that WA_EMBEDDED_SIGNUP FINISH was received and the backend provisioning completed.