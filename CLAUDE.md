IMPORTANT: DO NOT REBUILD OR REFACTOR THE EXISTING META WHATSAPP EMBEDDED SIGNUP FLOW.

The current flow has already reached a working point. Your ONLY job now is to make the flow continue from the point where it currently stops.

==================================================
CURRENT WORKING STATE — DO NOT BREAK THIS
==================================================

These parts are already working and MUST remain exactly functional:

1. Facebook SDK initializes successfully.

2. Meta Embedded Signup popup opens successfully.

3. Config ID is correct and currently used:
   2432311603846818

4. FB.login is launching the official WhatsApp Embedded Signup flow.

5. The OAuth redirect message is being received.

6. The OAuth code is successfully extracted from the non-JSON redirect message.

Current successful logs:

[EmbeddedSignup] WINDOW MESSAGE RECEIVED

origin:
https://www.facebook.com

[EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)

[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs

[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

DO NOT MODIFY THIS PART.

DO NOT remove the non-JSON OAuth fallback parser.

DO NOT change the Config ID.

DO NOT change the App ID.

DO NOT change response_type.

DO NOT change sessionInfoVersion.

DO NOT change the current popup implementation.

DO NOT replace FB.login with another OAuth implementation.

DO NOT change redirect_uri.

DO NOT change unrelated authentication, bots, notifications, billing, database, or other integrations.

==================================================
THE ONLY CURRENT PROBLEM
==================================================

After the OAuth code is received, the flow stops here:

[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs

The application is waiting for:

- waba_id
- phone_number_id
- business_id

but these values are not being captured, or the current listener is not correctly recognizing the Meta Embedded Signup completion/session message.

THIS IS THE ONLY PART YOU SHOULD FIX.

==================================================
IMPORTANT: DO NOT ASSUME THE CURRENT EVENT FORMAT
==================================================

Inspect the actual existing window.message listener.

The current OAuth message is:

event.data = string

and contains:

code=...

The WhatsApp Embedded Signup completion/session message may have a different structure.

Handle the legitimate Meta Embedded Signup message format correctly.

Safely inspect incoming messages from legitimate Meta/Facebook origins.

For debugging, log only safe metadata such as:

origin
typeof data
keys
type
event
version
data keys

NEVER log:

OAuth code
access token
client secret
app secret
full sensitive payload

==================================================
DO NOT WAIT FOR TWO EVENTS IN THE SAME MESSAGE
==================================================

The OAuth code and the Embedded Signup session information may arrive separately.

Treat them independently.

Maintain these values during the current signup attempt:

oauthCode
wabaId
phoneNumberId
businessId

If OAuth code arrives first:
    store it and continue listening.

If WABA/phone information arrives later:
    store it.

If WABA/phone information arrives first:
    store it.

Do NOT clear one when the other arrives.

Once the required information is available, continue automatically to the existing backend callback.

==================================================
DO NOT TREAT THIS AS AN ERROR
==================================================

The log:

[EmbeddedSignup] FB.login returned without a code. status: connected

MUST NOT stop the flow.

The actual OAuth code is already arriving through the window.message fallback.

Therefore:

FB.login response without code + status connected
=
continue waiting for the message event.

Do NOT show an error in this situation.

==================================================
FIX THE MISSING EMBEDDED SIGNUP SESSION EVENT
==================================================

Find out why the application currently does not capture the:

WA_EMBEDDED_SIGNUP

completion/session event.

Check:

- event.origin filtering
- event.data parsing
- JSON parsing
- nested data structures
- event.type
- event.event
- event.data
- data.waba_id
- data.phone_number_id
- data.business_id
- any official Embedded Signup event structure already used by the current implementation

Do not invent IDs.

Do not derive IDs from the OAuth code.

Do not hard-code WABA IDs or phone IDs.

Capture the actual IDs delivered by Meta.

==================================================
IMPORTANT: ORIGIN
==================================================

The OAuth redirect message is currently coming from:

https://www.facebook.com

The existing listener must not only assume:

https://oauth.facebook.com

Support the legitimate Meta/Facebook origins required by the official Embedded Signup flow.

BUT:

DO NOT use:

origin === "*"

Do not weaken postMessage security.

Use an explicit trusted-origin check.

==================================================
AFTER THE SESSION DATA IS RECEIVED
==================================================

Do NOT create a new backend flow.

Use the EXISTING backend endpoint:

POST /api/integrations/meta/oauth/callback

Send the already received:

code
redirect_uri
waba_id
phone_number_id
business_id

according to the existing API contract.

The backend should then continue using its existing Meta OAuth/integration logic.

If the backend already supports server-side discovery as a fallback, keep it.

But if the frontend already has the real WABA/phone IDs from Embedded Signup, pass those IDs to the backend instead of forcing unnecessary discovery.

==================================================
PREVIOUS BACKEND ERROR
==================================================

Previously the backend reached:

Step 1/5 - Meta token exchange succeeded

but then failed on:

GET /me/businesses

with:

(#100) Missing Permission

This should NOT happen unnecessarily when the Embedded Signup flow has already provided the WABA/phone identifiers.

Use the supplied IDs where available.

Do not remove valid fallback logic.

Do not bypass Meta permissions.

Do not fake IDs.

==================================================
CALLBACK MUST HAPPEN ONLY AFTER REQUIRED DATA EXISTS
==================================================

Do not submit an incomplete callback simply because the OAuth code exists.

Do not submit:

waba_id = fake
phone_number_id = fake

Instead:

1. Receive OAuth code.
2. Receive Embedded Signup session information.
3. Extract actual WABA/phone IDs.
4. Combine the stored values.
5. Call the existing backend callback.
6. Handle the backend response.
7. Show Connected only after backend confirms success.

==================================================
PREVENT DUPLICATE CALLBACKS
==================================================

The same OAuth code must not be exchanged multiple times.

Use a per-attempt guard.

For example:

callbackStarted = true

once the backend callback begins.

Reset this only when the user starts a completely new signup attempt.

==================================================
DO NOT USE A 12-SECOND FAILURE AS THE MAIN LOGIC
==================================================

The current:

WA_EMBEDDED_SIGNUP FINISH event never arrived

timeout should not be used to prematurely terminate a valid signup flow.

Do not simply increase the timeout.

Fix the actual event listener/parser.

If a timeout is still required, it should only be a final safety fallback and should report which exact values are missing.

Example safe diagnostics:

oauthCodeReceived: true
wabaIdReceived: false
phoneNumberIdReceived: false
businessIdReceived: false

Never print the actual code/token.

==================================================
SUCCESS CONDITION
==================================================

The desired flow is:

Launch Embedded Signup
        ↓
Meta popup opens
        ↓
User completes WhatsApp setup
        ↓
OAuth code received
        ↓
WA Embedded Signup session/completion event received
        ↓
WABA ID extracted
        ↓
Phone Number ID extracted
        ↓
Business ID extracted if available
        ↓
Existing backend callback
        ↓
Meta token exchange
        ↓
WhatsApp assets validated
        ↓
Integration saved
        ↓
Frontend shows:
WhatsApp Connected

==================================================
VERY IMPORTANT: PRESERVE EVERYTHING BEFORE THIS POINT
==================================================

Before changing anything:

1. Inspect the existing implementation.
2. Identify exactly where OAuth code is currently extracted.
3. DO NOT modify that working code.
4. Identify exactly where the application waits for WA_EMBEDDED_SIGNUP.
5. Modify ONLY that missing portion.
6. Keep the existing backend endpoint.
7. Keep existing authentication/session handling.
8. Keep existing database save logic.
9. Keep all unrelated functionality untouched.

Do NOT refactor the entire component.

Do NOT rewrite the entire Meta integration.

Do NOT replace working code unnecessarily.

Make the SMALLEST possible change that makes the flow continue.

==================================================
FINAL VERIFICATION
==================================================

After implementing the change, test the actual flow end-to-end.

The console should progress beyond:

LOGIN_CODE_RECEIVED

and should show something equivalent to:

[EmbeddedSignup] WA_EMBEDDED_SIGNUP event received

[EmbeddedSignup] WABA ID received

[EmbeddedSignup] Phone Number ID received

[EmbeddedSignup] Submitting signup data to backend

Then the backend should return success.

If the event still does not arrive, DO NOT make random changes.

Instead provide the exact safe diagnostic output showing:

- message origin
- data type
- message keys
- type
- event
- version
- data keys

and identify exactly what event Meta is sending and why the current listener does not recognize it.

IMPORTANT:
Do not claim the integration is fixed unless the complete flow reaches backend success and the WhatsApp integration is actually saved/connected.