I need you to fix and complete ONLY the WhatsApp Embedded Signup integration in my existing ORVYM SaaS application and make it fully working end-to-end.

DO NOT modify, refactor, redesign, or touch any unrelated ORVYM functionality.

This is a targeted production bug fix.

==================================================
CURRENT STATUS
==============

Facebook SDK is working:

Facebook SDK initialized with App ID: 3862862217342382

Embedded Signup opens successfully:

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login (JS SDK)
App ID: 3862862217342382
Config ID: 2432311603846818

Meta sends:

event: SDK_QUERY_STRING

The actual payload is:

query-string with keys:
["cb","domain","is_canvas","origin","relation","frame","code","base_domain"]

The exchangeable authorization code is successfully received:

[EmbeddedSignup] code received: yes (length 451)

FB.login also returns:

[EmbeddedSignup] FB.login response status: connected

Therefore, Facebook SDK initialization, App ID, Config ID, Embedded Signup launch, Meta authorization, and exchangeable code reception are already working.

==================================================
IMPORTANT DISCOVERY
===================

DO NOT try to extract:

* waba_id
* phone_number_id
* business_id

from the `SDK_QUERY_STRING` event.

The actual payload does NOT contain these fields.

It contains the exchangeable `code`.

Therefore the correct architecture is:

Embedded Signup
↓
SDK_QUERY_STRING
↓
Extract exchangeable code
↓
Send code to existing ORVYM backend
↓
Backend performs the required Meta code/token exchange
↓
Backend uses the resulting authorization/token
↓
Backend retrieves/validates the connected WhatsApp Business information
↓
Get:
business_id
waba_id
phone_number_id
↓
Save/process through the EXISTING ORVYM integration flow
↓
Frontend shows WhatsApp Connected

==================================================
YOUR TASK
=========

Make this complete flow actually work.

Do not stop after receiving the code.

Trace and fix everything AFTER the 451-character code is received.

Inspect the existing codebase and determine:

1. Where the exchangeable code is received.
2. Where it is supposed to be sent.
3. Which backend endpoint receives it.
4. Whether that request is actually being made.
5. Whether the backend receives the code correctly.
6. Whether the backend successfully performs the required Meta exchange.
7. Whether the resulting authorization/token is valid.
8. Whether the backend can retrieve the connected Business/WABA/Phone information.
9. Whether the result is returned to the frontend.
10. Whether the existing ORVYM connection flow saves/displays the connection correctly.

Fix the actual broken point.

Do not guess.

==================================================
FRONTEND
========

Keep the existing Facebook SDK and Embedded Signup implementation.

The frontend should:

1. Launch FB.login exactly once per user click.
2. Receive SDK_QUERY_STRING.
3. Parse the query string correctly.
4. Extract the exchangeable `code`.
5. Prevent processing the same code more than once.
6. Send the code to the existing backend integration endpoint.
7. Wait for the backend result.
8. Update the existing connection state.
9. Allow retry if the signup is cancelled or fails.

Do NOT require WABA ID, Phone Number ID, or Business ID from SDK_QUERY_STRING.

Do NOT hardcode any IDs.

==================================================
DUPLICATE FB.LOGIN
==================

The current logs previously showed Embedded Signup launching more than once.

Find and fix the reason.

Check:

* duplicate click handlers
* useEffect
* component mounting
* React StrictMode
* duplicate SDK initialization
* duplicate event listeners
* callbacks
* state changes

Required:

ONE CLICK
→ ONE FB.login()
→ ONE Embedded Signup
→ ONE CODE
→ ONE BACKEND EXCHANGE

Do not permanently disable reconnect/retry.

==================================================
BACKEND
=======

This is the most important part.

Inspect the existing backend implementation that handles the Embedded Signup exchangeable code.

Do NOT create an unnecessary new architecture if an existing endpoint/service already exists.

Trace:

Frontend
→ existing backend endpoint
→ Meta API
→ response
→ existing ORVYM connection flow

If the endpoint is incorrect, fix it.

If the Meta exchange implementation is incorrect, fix it.

If the Meta API request is incorrect, fix it.

If WABA discovery is missing, implement it only within the existing WhatsApp integration flow.

If the backend already has WABA discovery logic, reuse it.

The backend must securely handle Meta credentials.

Never expose:

* App Secret
* access tokens
* client secrets

to the frontend.

==================================================
WABA / PHONE / BUSINESS INFORMATION
===================================

After processing the exchangeable code, the backend must obtain/validate the actual connected WhatsApp account information from Meta.

Required information:

* Business ID
* WABA ID
* Phone Number ID
* Display phone number where available

Do NOT fabricate these values.

Do NOT hardcode them.

Do NOT expect them from SDK_QUERY_STRING.

Obtain them through the appropriate backend/Meta flow after processing the authorization code.

==================================================
ORVYM CONNECTION
================

Once Meta authorization and account discovery succeed, continue using the EXISTING ORVYM WhatsApp connection mechanism.

Do not redesign the database.

Do not redesign the tenant system.

Do not redesign webhooks.

Do not redesign messaging.

Use the existing implementation.

The only goal is to make the existing WhatsApp connection flow complete successfully.

==================================================
DO NOT TOUCH THESE
==================

DO NOT modify:

* ORVYM dashboard
* UI design
* AI
* chatbot
* inbox
* campaigns
* analytics
* billing
* subscriptions
* authentication
* tenant architecture
* database architecture
* existing webhook architecture
* existing messaging logic
* unrelated APIs
* unrelated components
* unrelated dependencies

Do not refactor unrelated code.

Make the smallest safe changes necessary.

==================================================
PRODUCTION
==========

Production frontend:

https://apps.orvym.com

Production backend:

https://orym-saas-application.onrender.com

Do not introduce localhost URLs into production.

Do not change the current App ID or Config ID unless you prove they are actually incorrect.

App ID:

3862862217342382

Config ID:

2432311603846818

==================================================
ERROR HANDLING
==============

Trace the real request/response flow.

If the backend returns an error, identify the exact Meta/API/backend error and fix it.

Handle:

* user cancellation
* missing code
* invalid code
* code exchange failure
* Meta API errors
* missing WABA
* missing phone number
* network errors
* duplicate processing

Do not hide errors.

Do not fake successful connection.

==================================================
SUCCESS CONDITION
=================

I consider this task complete ONLY when this works:

User opens ORVYM
→ clicks Connect WhatsApp
→ Embedded Signup opens
→ user completes Meta onboarding
→ exchangeable code is received
→ code is sent to backend
→ backend successfully processes the code
→ backend obtains the authorized WhatsApp Business information
→ existing ORVYM WhatsApp connection is completed
→ frontend receives success
→ WhatsApp shows CONNECTED
→ page refresh still shows the correct existing connection
→ user can retry if signup fails/cancels

The `SDK_QUERY_STRING` event does NOT need to contain WABA ID, Phone ID, or Business ID.

Only the exchangeable code needs to come from that event.

==================================================
VERY IMPORTANT
==============

Do not tell me only what I should change.

Inspect the existing codebase and IMPLEMENT THE FIX.

Do not stop at:

"code received successfully."

Continue through:

CODE
→ BACKEND
→ META EXCHANGE
→ WABA DISCOVERY
→ PHONE DISCOVERY
→ EXISTING ORVYM CONNECTION
→ SUCCESS

If something is already implemented, reuse it.

If something is broken, fix it.

If something is missing and is required specifically for Embedded Signup to complete, implement it.

Do not touch anything unrelated.

==================================================
FINAL REPORT
============

After implementation, report:

1. Exact root cause
2. Files changed
3. Exact changes made
4. Code → backend flow
5. Meta exchange flow
6. How WABA/Phone/Business IDs are obtained
7. Duplicate FB.login fix
8. Whether production configuration needs any change
9. What was tested
10. Any remaining blocker

Do not give a theoretical answer.

IMPLEMENT AND VERIFY THE FIX.
