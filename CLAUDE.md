We need to FIX the remaining WhatsApp Embedded Signup issue in the EXISTING ORVYM application.

IMPORTANT:
Do NOT rewrite or replace the existing Meta OAuth / WhatsApp integration.
Do NOT break anything that is already working.
Make the smallest safe changes necessary and preserve the current working flow.

CURRENT STATUS:
The official Meta WhatsApp Embedded Signup popup is now opening correctly.

The following are already working:
1. Facebook SDK initializes successfully.
2. App ID is correct: 3862862217342382
3. WhatsApp Embedded Signup launches through FB.login.
4. Config ID is correct: 2432311603846818
5. response_type = "code"
6. override_default_response_type = true
7. sessionInfoVersion = 3
8. User can reach the Meta Business selection / permissions screens.
9. Meta returns an exchangeable OAuth code.
10. Backend receives the OAuth code.
11. Backend successfully exchanges the code for an access token.
12. Existing backend endpoint:
   POST /api/integrations/meta/oauth/callback
   is working up to the token-exchange stage.

DO NOT CHANGE THESE WORKING PARTS UNNECESSARILY.

CURRENT ERROR:

Frontend logs show:

[EmbeddedSignup] Message listener registered
[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)
[EmbeddedSignup] WINDOW MESSAGE RECEIVED
origin: https://oauth.facebook.com
dataType: string
rawData: cb=...&domain=apps.orvym.com&...&code=...
[EmbeddedSignup] PARSED MESSAGE: non-JSON string (ignored)
[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)
[EmbeddedSignup] code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)
[EmbeddedSignup] WA_EMBEDDED_SIGNUP FINISH event never arrived - showing onboarding error

Timeout diagnostics:
popup_since: attempt started, WA_EMBEDDED_SIGNUP session not delivered within 12s
messages_received: []
saw_WA_EMBEDDED_SIGNUP_event: false
saw_CANCEL: false
saw_ERROR: false
sessionInfoVersion_requested: 3
config_id: 2432311603846818

BACKEND LOGS:

Step 1/5 - Meta token exchange succeeded
Access token received: YES

The previous backend attempt to discover WABA through:
GET /v26.0/me/businesses
returned:

(#100) Missing Permission

However, the immediate frontend issue is that the WhatsApp Embedded Signup session event is not being captured.

ROOT CAUSE TO INVESTIGATE:

The frontend is receiving the OAuth redirect message containing the exchangeable "code", but it is treating the non-JSON OAuth redirect message as irrelevant.

The implementation must correctly support the official Meta WhatsApp Embedded Signup postMessage/session event flow.

The frontend must listen for the WhatsApp Embedded Signup event without breaking the OAuth code flow.

REQUIRED FIX:

1. Inspect the existing Embedded Signup implementation.

2. Keep the existing OAuth code handling exactly as a fallback/parallel path.

3. Improve the window message listener so it can correctly distinguish:

   A) OAuth redirect-back messages containing:
      code=...

   B) WhatsApp Embedded Signup session messages containing the official
      WA_EMBEDDED_SIGNUP event/session information.

4. Do NOT assume every message is JSON.

5. For string messages:
   - safely inspect the string
   - parse URL/query-string style messages when appropriate
   - do not discard useful Meta Embedded Signup messages simply because JSON.parse() fails.

6. For object messages:
   - inspect the event payload safely
   - support the official Meta event structure
   - detect the WhatsApp Embedded Signup completion event.

7. Validate the message origin securely.
   The implementation should accept the official Meta OAuth/Embedded Signup origins required by the current Meta flow, while NOT accepting arbitrary origins.

8. Do NOT rely exclusively on:
      event.data.event === "WA_EMBEDDED_SIGNUP"

   Instead, inspect the actual Meta Embedded Signup payload structure and support the event/session structure returned by the current flow.

9. When the WhatsApp Embedded Signup completion event is received, extract and store the available:
   - waba_id
   - phone_number_id
   - business_id if available
   - any other official session asset identifiers required by the backend.

10. The frontend should NOT show an onboarding timeout merely because the OAuth code arrives before the session event.

11. Increase/remove the overly aggressive 12-second timeout.
    The Meta popup/user interaction can take longer than 12 seconds.
    Replace it with a safe timeout only if necessary, preferably based on popup closure / actual flow completion rather than an arbitrary 12-second timer.

12. IMPORTANT:
    If the OAuth code has already been received but waba_id / phone_number_id have not yet arrived, keep waiting for the official Embedded Signup event instead of immediately failing.

13. Once both pieces are available:
    - OAuth code
    - WhatsApp session asset IDs

    send them to the existing backend callback endpoint.

14. If the session event arrives before the OAuth code, store the session IDs temporarily and wait for the OAuth code.
    If the OAuth code arrives first, store the code temporarily and wait for the session IDs.

15. Only call the backend once all required values are available.

16. Preserve the existing backend API contract unless absolutely necessary.

17. Do NOT remove the current fallback where the backend can resolve IDs server-side.

18. DO NOT remove or weaken existing security checks.

BACKEND FIX:

The backend currently tries:

GET /v26.0/me/businesses

and receives:
(#100) Missing Permission

Do NOT blindly add random permissions or replace the existing OAuth implementation.

Instead:

A) Inspect which permissions/scopes are actually granted by the Embedded Signup access token.

B) Inspect the official current Meta Embedded Signup flow and determine the correct way to obtain the WABA ID and phone number ID from the Embedded Signup result/session.

C) Prefer the WABA ID / phone number ID supplied by the Embedded Signup session event rather than relying on /me/businesses.

D) Keep the existing server-side discovery only as a fallback.

E) If server-side fallback requires a permission that is not actually available to the Embedded Signup token, handle that gracefully instead of making the whole integration fail.

F) Do not expose access tokens, client secrets, or sensitive Meta credentials in logs.

IMPORTANT UI REQUIREMENT:

The Meta Embedded Signup popup must remain the official Meta flow.

Do NOT replace it with a custom fake popup.

Do NOT change the existing FB.login/config_id implementation unless required for the event handling fix.

The current popup is working and reaches:

"Choose the Businesses you want ORVYM LABS to access"

and the permissions/review screen.

Keep this behavior exactly as it is.

TESTING REQUIREMENTS:

After making the fix, test this complete sequence:

1. User opens ORVYM integrations.
2. User clicks Connect WhatsApp.
3. Official Meta Embedded Signup popup opens.
4. User selects/continues with Business.
5. User grants the requested WhatsApp permissions.
6. Meta Embedded Signup completes.
7. Browser receives WA_EMBEDDED_SIGNUP/session event.
8. Browser receives OAuth code.
9. Frontend combines the code + session IDs.
10. Frontend sends the existing backend callback request.
11. Backend exchanges code successfully.
12. Backend uses the supplied WABA ID / phone number ID.
13. WhatsApp integration is saved.
14. UI shows Connected/Success.
15. No 12-second false timeout occurs.
16. No "WA_EMBEDDED_SIGNUP FINISH event never arrived" error occurs.

VERY IMPORTANT REGRESSION RULE:

Before changing code, inspect the current implementation and identify exactly where:
- FB.login is initialized
- message listener is registered
- OAuth code is extracted
- WA_EMBEDDED_SIGNUP event is expected
- 12-second timeout is triggered
- backend callback is called

Modify only the necessary sections.

Do not rewrite unrelated files.
Do not change authentication.
Do not change database models unless required.
Do not change existing working OAuth token exchange.
Do not change the App ID.
Do not change the Config ID.
Do not change the redirect URI.

AFTER IMPLEMENTATION:

Provide:
1. Exact files changed.
2. Exact reason for each change.
3. The final Meta Embedded Signup event-handling logic.
4. Confirmation that OAuth code handling remains intact.
5. Confirmation that the 12-second false timeout is fixed.
6. Confirmation that WABA ID and phone number ID are obtained from the Embedded Signup session when available.
7. Any Meta App Dashboard permissions/configuration still required.

Do not claim success until the complete flow is tested end-to-end.