IMPORTANT — REPLACE THE CURRENT CUSTOM EMBEDDED SIGNUP WITH META'S OFFICIAL IMPLEMENTATION

I do NOT want the current custom ORVYM Embedded Signup implementation patched anymore.

Temporarily COMMENT OUT the current Embedded Signup implementation and implement Meta's official documented Embedded Signup flow instead.

DO NOT DELETE the old code.
Keep the old implementation commented out so it can be restored if necessary.

==================================================
1. CURRENT CUSTOM IMPLEMENTATION — COMMENT OUT
==================================================

Find and COMMENT OUT the current code responsible for:

- FB.login() Embedded Signup launch
- current config_id launch implementation
- custom window.message listener
- custom SDK_QUERY_STRING parsing
- custom OAuth code extraction
- custom WA_EMBEDDED_SIGNUP parsing
- custom redirect_uri handling
- custom Meta OAuth/token exchange logic related to this flow

Do NOT delete it.

Do NOT continue adding fixes to this old implementation.

==================================================
2. USE META OFFICIAL EMBEDDED SIGNUP IMPLEMENTATION
==================================================

Use Meta's official Embedded Signup implementation from:

https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/implementation

Use the official implementation pattern rather than our custom implementation.

The Meta configuration is:

APP ID:
3862862217342382

CONFIG ID:
2432311603846818

Production:
https://apps.orvym.com

==================================================
3. OFFICIAL META EMBEDDED SIGNUP LAUNCH
==================================================

Implement the official Meta JS SDK flow.

The official flow should be equivalent to:

FB.login(function(response) {
    if (response.authResponse) {
        console.log("Embedded Signup completed");
    } else {
        console.log("Embedded Signup cancelled");
    }
}, {
    config_id: "2432311603846818",
    response_type: "code",
    override_default_response_type: true,
    extras: {
        setup: {},
        sessionInfoVersion: 3
    }
});

IMPORTANT:

Do NOT blindly copy this snippet if the current Meta documentation specifies a newer syntax/version.

Use the CURRENT official Meta documentation implementation corresponding to the configured Embedded Signup version.

The code above is the reference structure only.

Do NOT invent additional redirect_uri logic.

Do NOT add redirect_uri fallbacks.

Do NOT make multiple OAuth attempts.

==================================================
4. OFFICIAL META MESSAGE EVENT HANDLING
==================================================

Use Meta's documented session logging/message event listener implementation.

The implementation must listen for the official:

WA_EMBEDDED_SIGNUP

session event

and correctly obtain the documented session information, including when provided:

- WABA ID
- Phone Number ID

Do NOT rely on the old custom SDK_QUERY_STRING parser.

Do NOT fabricate WABA ID, Phone Number ID, or Business ID.

Follow the exact event structure documented by Meta.

The listener must:

- verify the event origin according to Meta's documentation
- parse the documented message format
- handle successful completion
- handle cancellation/failure
- avoid duplicate processing

==================================================
5. IMPORTANT — DO NOT WAIT FOREVER FOR SESSION DATA
==================================================

The exchangeable authorization code and the Embedded Signup session information are separate pieces of information.

Do not create a race condition where:

code is received
↓
frontend waits forever
↓
backend exchange never happens

Implement Meta's documented event flow correctly.

If Meta's current documentation specifies that the WABA/phone information should be obtained through session logging or API requests, follow that exact mechanism.

==================================================
6. BACKEND — USE META'S OFFICIAL ONBOARDING FLOW
==================================================

Use the official Meta documentation:

"Onboarding business customers as a Tech Provider or Tech Partner"

The documented flow is:

Embedded Signup
↓
exchange code
↓
business token
↓
WABA
↓
subscribe WABA
↓
phone registration if required

==================================================
7. STEP 1 — TOKEN EXCHANGE
==================================================

Use Meta's documented server-to-server request:

GET:

https://graph.facebook.com/<API_VERSION>/oauth/access_token

Parameters:

client_id=<APP_ID>
client_secret=<APP_SECRET>
code=<CODE>

Reference implementation:

curl --get \
'https://graph.facebook.com/v21.0/oauth/access_token' \
-d 'client_id=<APP_ID>' \
-d 'client_secret=<APP_SECRET>' \
-d 'code=<CODE>'

IMPORTANT:

Use the API version appropriate for the current Meta documentation.

Our backend currently uses v26.0. Do not downgrade blindly.

Verify the current supported API version before implementation.

MOST IMPORTANT:

Do NOT add the old redirect_uri parameter unless the CURRENT official Meta Embedded Signup documentation explicitly requires it for this exact flow.

Do not use:

- https://apps.orvym.com
- https://apps.orvym.com/dashboard/integrations
- https://apps.orvym.com/dashboard/integrations/
- https://www.facebook.com/connect/login_success.html

as random fallbacks.

Use exactly what Meta's official flow requires.

==================================================
8. APP SECRET SECURITY
==================================================

APP_SECRET must NEVER be sent to the frontend.

The token exchange MUST happen server-to-server.

Frontend only sends the exchangeable code/session information to the existing backend.

==================================================
9. STEP 2 — WABA
==================================================

Use Meta's official method to obtain the customer's:

WABA ID

The documentation states this can be obtained through:

- Embedded Signup session logging
OR
- appropriate API request

Use the method appropriate to the actual Embedded Signup implementation.

Do NOT hardcode WABA ID.

==================================================
10. STEP 3 — SUBSCRIBE WABA
==================================================

Use the official Meta endpoint:

POST

https://graph.facebook.com/<API_VERSION>/<WABA_ID>/subscribed_apps

Authorization:

Bearer <BUSINESS_TOKEN>

Expected response:

{
    "success": true
}

Use the business token returned from the official token exchange.

==================================================
11. STEP 4 — PHONE NUMBER
==================================================

Obtain the customer's:

BUSINESS PHONE NUMBER ID

using Meta's documented Embedded Signup/session/API mechanism.

Do NOT expect it from the old SDK_QUERY_STRING implementation.

Do NOT hardcode it.

==================================================
12. STEP 5 — REGISTER PHONE
==================================================

If phone registration is required for the customer's flow, use Meta's official Register API:

POST

https://graph.facebook.com/<API_VERSION>/<BUSINESS_CUSTOMER_PHONE_NUMBER_ID>/register

Authorization:

Bearer <BUSINESS_TOKEN>

Body:

{
    "messaging_product": "whatsapp",
    "pin": "<DESIRED_PIN>"
}

Do NOT invent a PIN.

If ORVYM already has a phone registration mechanism, reuse it.

==================================================
13. EXISTING ORVYM CONNECTION
==================================================

After Meta onboarding succeeds:

Business Token
↓
WABA ID
↓
Phone Number ID
↓
existing ORVYM WhatsApp connection

Reuse the existing ORVYM database/connection mechanism.

DO NOT redesign:

- database
- tenant architecture
- webhooks
- messaging
- dashboard
- inbox
- AI
- chatbot
- campaigns
- analytics
- billing
- authentication

==================================================
14. CURRENT ERROR — DO NOT PATCH IT AGAIN
==================================================

The current implementation repeatedly produces:

Error Code: 100
Error Subcode: 36008
OAuthException

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

STOP PATCHING THE CURRENT IMPLEMENTATION.

The purpose of this task is to:

COMMENT OUT OLD CUSTOM IMPLEMENTATION

and replace it with:

OFFICIAL META IMPLEMENTATION

Do NOT add:

- multiple redirect_uri attempts
- retry with different redirect_uri
- random URL fallbacks
- custom OAuth workarounds
- fake success responses

==================================================
15. IMPORTANT — PRESERVE EVERYTHING ELSE
==================================================

Only change the WhatsApp Embedded Signup/onboarding implementation.

Everything unrelated must remain untouched.

Make the smallest possible change.

==================================================
16. TEST
==================================================

Test the complete flow:

User opens ORVYM
↓
Connect WhatsApp
↓
Official Meta Embedded Signup
↓
Customer completes onboarding
↓
Meta official completion/session event
↓
Exchangeable code
↓
Backend
↓
Meta official token exchange
↓
Business Token
↓
WABA ID
↓
Phone Number ID
↓
WABA subscribed_apps
↓
Phone registration if required
↓
Existing ORVYM connection
↓
CONNECTED

Do not consider the task complete merely because:

LOGIN_CODE_RECEIVED

appears.

The complete backend onboarding must succeed.

==================================================
17. FINAL REPORT
==================================================

After implementation report:

1. Exact old Embedded Signup code commented out
2. Files changed
3. Exact Meta official implementation added
4. Meta Embedded Signup version used
5. Token exchange endpoint/version
6. Whether redirect_uri is required or not according to the official flow
7. WABA ID source
8. Phone Number ID source
9. WABA subscription result
10. Phone registration result
11. Final ORVYM connection result
12. Test result
13. Any remaining blocker

DO NOT ONLY EXPLAIN.

IMPLEMENT THE OFFICIAL META FLOW.