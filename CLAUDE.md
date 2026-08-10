FINAL TASK — FIX META WHATSAPP EMBEDDED SIGNUP END-TO-END

You are working on my existing ORVYM WhatsApp SaaS application.

I need you to FIX the Meta WhatsApp Embedded Signup integration completely and make the REAL end-to-end flow work in production.

IMPORTANT:
Do NOT make another speculative patch.
Do NOT declare success because the code compiles or FB.login returns a code.
Do NOT work around Meta's requirements.
Implement the CURRENT OFFICIAL META FLOW according to the project's requirements/docs and Meta's current official documentation.

==================================================
1. FIRST: READ THE PROJECT DOCUMENTATION
==================================================

Before changing code, inspect and read:

- CLAUDE.md
- IMPLEMENTATION_SUMMARY.md
- any Meta/WhatsApp integration documentation in the repository
- existing backend/services/meta_oauth.py
- existing Meta integration router
- existing frontend Embedded Signup implementation
- environment/configuration files (DO NOT expose secrets)
- existing webhook implementation
- existing WhatsApp integration/database models

Understand the current architecture before modifying anything.

==================================================
2. CURRENT PRODUCTION ARCHITECTURE
==================================================

Frontend:
Hostinger

Backend:
Render

Backend Render region:
Ohio, USA

Database:
Neon

Production frontend:
https://apps.orvym.com

Production backend:
https://orym-saas-application.onrender.com

Meta App ID:
3862862217342382

Meta Config ID:
2432311603846818

The application is a WhatsApp SaaS where users should be able to connect their WhatsApp Business account through Meta Embedded Signup without manually entering Phone Number ID/access token.

==================================================
3. CURRENT PROBLEM
==================================================

The current frontend successfully launches Meta Embedded Signup.

Current logs show:

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup
Config ID: 2432311603846818
response_type: code
override_default_response_type: true
extras: {"setup":{},"sessionInfoVersion":3}

Meta successfully sends an OAuth exchangeable code:

[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

The raw window.message comes from:

https://oauth.facebook.com

and contains:

domain=apps.orvym.com
origin=https://apps.orvym.com/...
code=...

Therefore:

FB.login() works.
Meta authorization works.
An exchangeable code is being received.

BUT:

WA_EMBEDDED_SIGNUP session event is NOT being received.

Current logs:

[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)

[EmbeddedSignup] WA_EMBEDDED_SIGNUP FINISH event never arrived

messages_received: []

saw_WA_EMBEDDED_SIGNUP_event: false

saw_CANCEL: false

saw_ERROR: false

sessionInfoVersion_requested: 3

The backend then cannot reliably obtain the WABA ID / Phone Number ID/session information.

Earlier we also received:

Meta error code: 100
Meta error subcode: 36008

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

Do NOT assume redirect_uri is the current root cause.

The current primary problem appears to be the Embedded Signup session event / asset ID delivery or incorrect handling/configuration of the Embedded Signup flow.

==================================================
4. CRITICAL VERSION CHECK
==================================================

Before changing implementation, VERIFY the actual Embedded Signup version associated with Config ID:

2432311603846818

The Meta documentation indicates that Embedded Signup v2 is scheduled for deprecation on October 15, 2026 and migration to Embedded Signup v4 is required.

VERIFY THIS AGAINST CURRENT OFFICIAL META DOCUMENTATION.

Determine:

A. Which Embedded Signup version the current Config ID uses.
B. Whether the Config ID is v2, v3, v4, or another current version.
C. Whether this Config ID is affected by the October 15, 2026 deprecation.
D. Whether a new/current Config ID must be created.
E. Whether sessionInfoVersion=3 is correct for the actual configured version.
F. Whether the current FB.login parameters are correct for that version.
G. Whether the current event/listener implementation matches Meta's official flow for that version.

DO NOT continue patching an obsolete implementation if Meta requires migration.

If a new Config ID is required, clearly explain exactly what must be configured in Meta App Dashboard and update the application to use the new configuration through environment variables/config rather than hardcoding it.

==================================================
5. VERIFY THE OFFICIAL META FLOW
==================================================

Use CURRENT official Meta documentation as the source of truth.

Verify the complete Embedded Signup flow.

The intended result is:

User clicks:
Connect WhatsApp Business

↓

Meta Embedded Signup opens

↓

User completes Meta onboarding

↓

Application receives the exchangeable OAuth code

AND the appropriate Embedded Signup session information/event

↓

Obtain:
- WABA ID
- Phone Number ID
- Business ID if required
- any other required session asset IDs

↓

Exchange the code using the exact parameters required by Meta for the CURRENT Embedded Signup version.

↓

Obtain the appropriate access token/business token.

↓

Perform all required WhatsApp Business API setup steps.

This may include, depending on the current official flow:

- WABA discovery
- phone number discovery
- subscribed_apps
- phone number registration
- webhook configuration/subscription
- required business/account setup

Do NOT assume these endpoints or sequence are mandatory.
VERIFY the exact requirements from CURRENT Meta documentation.

↓

Save the integration in our database.

↓

Show:

WhatsApp Connected
Phone Number
WABA/business information
Webhook status

The complete flow must work without the user manually entering:
- access token
- Phone Number ID
- WABA ID

unless Meta's current official flow explicitly requires a fallback.

==================================================
6. FIX THE FRONTEND EVENT HANDLING
==================================================

Inspect the current window.message listener carefully.

The latest raw message from Meta is a non-JSON string.

Example:

cb=...&domain=apps.orvym.com&is_canvas=false&origin=https%3A%2F%2Fapps.orvym.com/...&relation=opener&frame=...&code=...

The application currently logs:

PARSED MESSAGE: non-JSON string (ignored)

This MUST be investigated.

Do not simply ignore non-JSON messages.

Verify the official format Meta uses for the Embedded Signup message.

Determine whether the current listener is:

- parsing the message incorrectly
- listening too late
- filtering the wrong origin
- expecting the wrong event structure
- expecting an obsolete event name
- using the wrong sessionInfoVersion
- using incorrect extras
- using an outdated SDK flow
- or missing another required listener/configuration.

The listener MUST be registered before launching FB.login().

Use the exact official event/message format required by Meta.

Do not invent a custom event.

Do not blindly accept arbitrary origins.

Use secure origin validation according to Meta's documented flow.

==================================================
7. FIX THE BACKEND TOKEN EXCHANGE
==================================================

Inspect:

backend/services/meta_oauth.py

and the OAuth callback endpoint.

Do NOT keep the previous speculative strategy of trying random redirect_uri values.

Do NOT send:

redirect_uri=""
or arbitrary URLs

unless CURRENT official Meta documentation explicitly requires that exact value for this exact flow.

The redirect_uri used during token exchange must exactly match what Meta recorded for the authorization request, according to the actual flow.

Determine the correct behavior from the current official documentation and implementation.

Also ensure:

- the code is exchanged exactly once
- the code is exchanged immediately
- the code is not retried after a failed/single-use exchange
- the frontend does not accidentally POST the same code multiple times
- timeout/retry logic cannot cause duplicate code exchanges

The code is short-lived and single-use.

==================================================
8. FIX SESSION DATA FLOW
==================================================

The frontend should not wait forever for:

WA_EMBEDDED_SIGNUP

if the current official Meta flow does not use that exact event name/version.

Determine the CURRENT official event mechanism.

If the event contains:

- WABA ID
- Phone Number ID
- business ID

capture them reliably.

Send the required session information to the backend along with the exchangeable code.

Validate all IDs server-side.

Do not trust arbitrary client-provided IDs without verification through Meta APIs.

==================================================
9. BACKEND WHATSAPP SETUP
==================================================

After successful token exchange:

Implement the CURRENT official Meta-required setup sequence.

Verify each API call against current Meta documentation.

Potential steps include:

1. Get/verify WABA
2. Get/verify phone number
3. Subscribe WABA/app using the required endpoint
4. Register phone number if required
5. Configure/verify webhook
6. Verify WhatsApp Business account state
7. Save integration

Do not implement fake success.

Every step must be validated using Meta's response.

If any step fails, return the actual Meta error with useful logging.

==================================================
10. WEBHOOK
==================================================

Verify the existing webhook implementation.

Ensure:

- webhook URL is publicly accessible
- verification endpoint works
- verify token is correct
- Meta can reach the endpoint
- required WhatsApp webhook fields are subscribed
- webhook subscription is completed using the correct current API flow

Do not break the existing WhatsApp bot while fixing Embedded Signup.

IMPORTANT:
There is already a WhatsApp bot/backend running.

Do NOT replace, disable, or break the existing bot functionality.

The Embedded Signup integration must be added/fixed without disrupting the existing WhatsApp messaging flow.

==================================================
11. DATABASE
==================================================

Inspect the existing integration database model.

Ensure the following can be persisted where required:

- WABA ID
- Phone Number ID
- Business ID
- access token/business token
- phone number
- webhook information
- connection status
- Meta account identifiers

Use the existing database architecture and migrations.

Do not create duplicate tables unnecessarily.

Do not expose access tokens in frontend logs.

==================================================
12. SECURITY
==================================================

Do not expose:

- META_APP_SECRET
- access tokens
- webhook secrets
- database credentials

in:

- browser logs
- frontend code
- Git
- API responses

Never log full OAuth codes or tokens.

Logging should only show safe metadata such as:

code length
WABA ID
Phone Number ID
Meta error code
Meta error subcode
fbtrace_id

==================================================
13. PRODUCTION CONFIGURATION
==================================================

Use environment variables.

Do not hardcode production secrets.

Verify these values/configurations:

META_APP_ID
META_APP_SECRET
META_CONFIG_ID
META_VERIFY_TOKEN
META webhook configuration
frontend URL
backend URL

If a new Config ID is required, update the environment configuration appropriately.

Remember:

Frontend:
https://apps.orvym.com

Backend:
https://orym-saas-application.onrender.com

==================================================
14. META APP DASHBOARD CHECK
==================================================

Inspect/verify the Meta App Dashboard configuration required by the CURRENT Embedded Signup version.

Check:

- App domains
- OAuth redirect configuration if applicable
- WhatsApp product
- Embedded Signup configuration
- Config ID
- allowed domains/origins
- required permissions
- webhook configuration
- Business Manager configuration
- required app permissions
- development/live mode requirements

If something must be changed manually in Meta Dashboard, STOP and tell me the exact setting/path/value required.

Do not pretend a code change can fix a dashboard configuration problem.

==================================================
15. PERMISSIONS / APP REVIEW
==================================================

The app will be submitted for Meta review.

Make sure the implementation actually uses the requested permissions/features.

Do not request unnecessary permissions.

Verify which permissions are required for:

- WhatsApp Business Account
- WABA management
- phone number management
- messaging
- webhook/subscription
- Embedded Signup

If App Review requires a screen recording, the actual production flow must be successfully demonstrable first.

==================================================
16. DO NOT BREAK EXISTING FUNCTIONALITY
==================================================

Before changing anything:

Understand the existing application.

Preserve:

- existing WhatsApp bot
- existing webhook
- existing integrations
- WooCommerce integration
- database functionality
- authentication
- frontend dashboard

Make minimal, clean changes where possible.

==================================================
17. TESTING REQUIREMENT
==================================================

Do NOT tell me:

"Syntax is correct, therefore fixed."

That is NOT sufficient.

Test as much of the complete flow as technically possible.

At minimum:

Backend:
- imports
- startup
- config endpoint
- OAuth callback
- Meta API calls
- database operations

Frontend:
- production build
- FB SDK initialization
- message listener
- Embedded Signup launch
- event parsing
- duplicate-code prevention

Integration:
- actual Meta Embedded Signup flow in browser

The final acceptance test is:

1. Open:
https://apps.orvym.com/dashboard/integrations

2. Click:
Connect WhatsApp Business

3. Meta Embedded Signup opens.

4. Complete onboarding.

5. OAuth code is received.

6. Session event/asset information is received.

7. WABA ID and Phone Number ID are obtained.

8. Backend exchanges the code successfully.

9. Required WhatsApp Business API setup succeeds.

10. Required webhook/subscription succeeds.

11. Integration is saved.

12. Dashboard shows:
WhatsApp Connected.

13. Existing WhatsApp bot continues working.

==================================================
18. ERROR HANDLING
==================================================

If anything fails, do NOT hide the error.

Log:

- HTTP status
- Meta error code
- Meta error subcode
- error type
- safe error message
- fbtrace_id
- which setup step failed

Never log:

- app secret
- access token
- full OAuth code

Frontend should display a useful user-friendly error.

==================================================
19. IMPORTANT: NO RANDOM WORKAROUNDS
==================================================

Do NOT:

- randomly try multiple redirect_uri values
- repeatedly exchange the same code
- fake WABA IDs
- fake Phone Number IDs
- bypass Meta permission checks
- ignore Meta errors
- accept arbitrary postMessage origins
- disable security validation
- hardcode tokens
- declare success based on local syntax checks
- implement an obsolete Embedded Signup version just because the existing code uses it

If Meta's current documentation contradicts the existing implementation, follow Meta's current official flow.

==================================================
20. FINAL DELIVERABLE
==================================================

After implementation, give me a concise report with:

1. Root cause of the current problem.
2. Embedded Signup version currently configured.
3. Whether the current Config ID is deprecated/affected.
4. Whether a new Config ID was required.
5. Exact frontend files changed.
6. Exact backend files changed.
7. Exact Meta Dashboard changes required.
8. Exact environment variables required.
9. Exact API sequence now implemented.
10. How the session event is handled.
11. How WABA ID and Phone Number ID are obtained.
12. How token exchange works.
13. How webhook/subscription is configured.
14. What tests were actually performed.
15. Whether the COMPLETE end-to-end flow was successfully tested.

MOST IMPORTANT:

Do not stop at "implementation complete."

The task is complete ONLY when the actual Meta Embedded Signup flow works end-to-end and the application reaches:

CONNECTED

with the real WABA ID + real Phone Number ID + valid Meta credentials/token + working webhook/subscription.

If you encounter a Meta Dashboard configuration or App Review requirement that cannot be changed through code, clearly tell me exactly what I must change manually instead of guessing.