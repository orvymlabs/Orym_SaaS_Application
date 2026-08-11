CRITICAL FIX — META WHATSAPP EMBEDDED SIGNUP OAUTH TOKEN EXCHANGE

We have now isolated the exact failure point from production logs.

DO NOT rewrite or redesign the existing WhatsApp Embedded Signup implementation.
DO NOT change the Config ID.
DO NOT change the Facebook SDK initialization.
DO NOT change the FB.login() flow.
DO NOT change sessionInfoVersion=3.
DO NOT change the existing postMessage listener unless absolutely required.
DO NOT break the parts that are already working.

CURRENT WORKING BEHAVIOR:

Frontend successfully does:

Facebook SDK initialized
FB.login() launched with Config ID 2432311603846818
response_type=code
override_default_response_type=true
extras includes sessionInfoVersion=3
oauth authorization code is successfully received
code length = 451

Therefore DO NOT touch these working parts unnecessarily.

EXACT CURRENT FAILURE:

Backend production logs show:

Parameter names:
['client_id', 'client_secret', 'code', 'redirect_uri']

redirect_uri included: True

redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Meta response:

HTTP 400
Error code: 100
Error subcode: 36008
Error type: OAuthException

Error message:
"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

The failure occurs at:

POST /api/integrations/meta/oauth/callback

services.meta_oauth

Step 1/6 Token exchange

IMPORTANT:
The Meta Tech Provider documentation we are following specifies the Embedded Signup token exchange as:

GET https://graph.facebook.com/{API_VERSION}/oauth/access_token

Parameters:
client_id=<APP_ID>
client_secret=<APP_SECRET>
code=<CODE>

The documented Step 1 does NOT include redirect_uri.

Therefore fix the backend token exchange so that the Embedded Signup authorization code is exchanged using ONLY:

client_id
client_secret
code

Do NOT send redirect_uri in this Embedded Signup token exchange request.

CURRENT BAD IMPLEMENTATION:

params = {
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": code,
    "redirect_uri": redirect_uri
}

CHANGE IT TO:

params = {
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": code
}

Do not append redirect_uri conditionally either.
For this Embedded Signup code-exchange path, redirect_uri must not be sent to Meta.

IMPORTANT SECURITY/RELIABILITY REQUIREMENTS:

1. The authorization code is short-lived and single-use.
2. Exchange it immediately after receiving it.
3. Do not exchange the same code twice.
4. Do not retry the same code automatically after a failed exchange.
5. Do not store/log the full OAuth code or business token.
6. Log only safe metadata such as code length, request stage, HTTP status and Meta error code/subcode.
7. Make sure the frontend calls the backend callback exactly once for each newly received code.
8. Prevent duplicate callback requests caused by React effects, rerenders, popup callbacks or message listeners.
9. Do not delay the code exchange while waiting for WABA/phone IDs if the code itself has already been received.

VERY IMPORTANT ABOUT SESSION INFORMATION:

The frontend currently receives the OAuth code through the oauth.facebook.com window message.

The existing logs show:

containsOAuthCode: true
containsWA_EMBEDDED_SIGNUP: false
containsSessionInfo: false
waba_id present: false
phone_number_id present: false
business_id present: false

Do NOT treat the absence of these IDs in the OAuth redirect string as an OAuth failure.

The implementation must correctly listen for Meta's WA_EMBEDDED_SIGNUP session event according to the current Embedded Signup implementation documentation.

The OAuth code and WA_EMBEDDED_SIGNUP session information are separate pieces of the flow.

DO NOT invent fake WABA IDs or phone_number IDs.

AFTER TOKEN EXCHANGE SUCCEEDS:

Continue the existing Meta Tech Provider onboarding flow:

STEP 1:
Exchange code for BUSINESS TOKEN.

STEP 2:
Use the business token + WABA ID to:

POST /{WABA_ID}/subscribed_apps

Expected:
{"success": true}

STEP 3:
Register the customer's business phone number:

POST /{PHONE_NUMBER_ID}/register

with:
{
  "messaging_product": "whatsapp",
  "pin": "<6-digit PIN>"
}

STEP 4:
Persist the successfully resolved:
- WABA ID
- phone_number_id
- business/customer business ID if available
- business token securely
- integration status

Then continue the existing webhook/message integration.

DO NOT implement the remaining onboarding steps until Step 1 is successfully fixed.

SESSION EVENT HANDLING:

Audit the existing window.message listener against Meta's official Embedded Signup session logging/message listener behavior.

The listener must:
- remain registered before FB.login()
- accept only the expected Meta origin(s)
- correctly handle Meta's actual event/message format
- correctly detect the WA_EMBEDDED_SIGNUP event
- extract session information when Meta sends it
- not ignore valid session messages simply because they are not JSON
- not mistake the oauth.facebook.com OAuth redirect string for the WA_EMBEDDED_SIGNUP session event
- not require WABA IDs to be present inside the OAuth redirect string itself

Do NOT simply parse every non-JSON OAuth redirect as a WA_EMBEDDED_SIGNUP event.
Keep OAuth code handling and session-event handling as separate paths.

CURRENT FRONTEND LOGIC:

It currently correctly detects:

OAuth code detected in non-JSON redirect message
code received
LOGIN_CODE_RECEIVED

The current problem is that after this the backend exchanges the code with an incorrect redirect_uri parameter.

Fix that first.

REDIRECT URI:

Do NOT remove or change the existing production redirect URI configuration from Meta App Dashboard unless investigation proves it is independently required.

Do NOT randomly change:

https://apps.orvym.com/dashboard/integrations/

Do not add/remove trailing slashes as a trial-and-error fix.

The primary fix for the current 36008 failure is:
REMOVE redirect_uri FROM THE BACKEND /oauth/access_token REQUEST FOR THIS EMBEDDED SIGNUP TOKEN EXCHANGE.

IMPORTANT:
There may be other OAuth flows in the application. Do not globally remove redirect_uri from unrelated OAuth integrations.

Scope the change specifically to:
WhatsApp Embedded Signup → authorization code → business token exchange.

REGRESSION SAFETY:

Before modifying anything:
- inspect the current implementation
- identify exact frontend Embedded Signup files
- identify exact backend Meta OAuth service/router
- identify all callers of the token exchange function
- identify whether any other Meta OAuth flow depends on redirect_uri

Make the smallest possible change.

Do NOT modify:
- authentication
- dashboard
- notifications
- conversations
- bots
- leads
- database schema unless absolutely necessary
- webhook verification
- existing WhatsApp messaging logic
- Facebook SDK initialization
- Config ID
- Embedded Signup popup behavior
- unrelated OAuth integrations

VALIDATION:

After implementation, test the production flow from a clean session.

Expected sequence:

1. User clicks Connect WhatsApp.
2. Facebook SDK initializes.
3. Embedded Signup popup opens.
4. Customer completes WhatsApp onboarding.
5. OAuth code is received.
6. Frontend sends the code ONCE to backend.
7. Backend logs:
   META GRAPH API TOKEN EXCHANGE
   parameters should be ONLY:
   client_id
   client_secret
   code
8. There must be NO:
   redirect_uri
   in the token exchange request.
9. Meta returns HTTP 200 and a business token.
10. Continue to WABA/session asset resolution.
11. Obtain WABA ID and phone_number_id through the correct Embedded Signup session mechanism/API.
12. Subscribe app to customer's WABA.
13. Register customer's phone number if required by the current onboarding flow.
14. Save integration successfully.
15. Existing WhatsApp messaging/webhooks continue working.

SUCCESS CRITERIA:

The current error:

Error code 100
Error subcode 36008
OAUTH_REDIRECT_URI_MISMATCH

must disappear.

Do not declare success merely because the popup opens or the OAuth code is received.

The actual success condition is:

OAuth code
→ business token
→ WABA ID
→ phone_number_id
→ subscribed app
→ registered/usable WhatsApp number
→ saved integration
→ messaging/webhooks working.

If Step 1 succeeds but Step 2/3 fails, report the exact next Meta API error rather than masking it.

FINAL REQUIREMENT:

Preserve everything that is already working.
Make the smallest targeted fix.
Do not rewrite the entire Embedded Signup implementation.
Do not introduce a second OAuth flow.
Do not create a fake fallback.
Do not bypass Meta.
Use the official Meta Embedded Signup / Tech Provider flow.