STOP making assumptions about redirect_uri.

The screenshot/logs prove that the backend previously hardcoded:

EXCHANGE_REDIRECT_URI =
https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46

This is a Meta internal SDK URL and MUST NOT be used as our OAuth redirect_uri.

I need you to fix the implementation according to the CURRENT OFFICIAL Meta WhatsApp Embedded Signup documentation and the project's requirements docs.

IMPORTANT:
- Do NOT add staticxx.facebook.com to Meta App Domains.
- Do NOT use an empty redirect_uri as a guessed fix.
- Do NOT try multiple random redirect_uri values.
- Do NOT use facebook.com/connect/login_success.html as another guess.
- Do NOT invent undocumented behavior.
- Do NOT change the working WhatsApp bot/integrations unrelated to Embedded Signup.

First inspect:
1. CLAUDE.md
2. all Meta/WhatsApp Embedded Signup documentation in the repository
3. current frontend Embedded Signup implementation
4. backend Meta OAuth implementation
5. current Config ID and its Embedded Signup version
6. Meta App configuration assumptions in the code

Then trace the COMPLETE official flow:

FB.login()
→ authorization code
→ WA_EMBEDDED_SIGNUP session event
→ WABA ID
→ Phone Number ID
→ business/system-user access token as required by the official flow
→ subscribed_apps
→ phone registration if required
→ webhook verification/subscription
→ save connected WhatsApp integration

The current frontend already receives an authorization code of length ~451, so DO NOT treat OAuth authorization as the missing part.

The current missing/problematic parts are:
1. correct official token/code exchange
2. correct handling of redirect_uri according to the exact Meta flow being used
3. WA_EMBEDDED_SIGNUP sessionInfoVersion/session event handling
4. extracting waba_id and phone_number_id from the session event
5. completing the remaining WhatsApp onboarding steps
6. correct permissions/token handling

CRITICAL:
Before changing code, determine from the CURRENT official Meta docs whether this specific FB.login(config_id, response_type=code, override_default_response_type=true) flow requires redirect_uri in the token exchange.

If Meta's current documentation says redirect_uri must be included, use ONLY the exact redirect URI that was actually used by the authorization request and ensure it is registered in the Meta App Dashboard.

If Meta's current documentation says redirect_uri must be omitted for this exact Embedded Signup flow, omit it completely.

Do not use "" as a workaround unless the official documentation explicitly requires it.

Also verify that the frontend launch mechanism and backend exchange mechanism are compatible. If the frontend is launching Embedded Signup through FB.login(), do not mix it with an unrelated OAuth dialog/token-exchange pattern.

SESSION EVENT REQUIREMENT:

Implement the official WA_EMBEDDED_SIGNUP postMessage/session event handling correctly.

We currently see:

LOGIN_CODE_RECEIVED
code received, waiting for WA_EMBEDDED_SIGNUP session asset IDs
WA_EMBEDDED_SIGNUP FINISH event never arrived

Investigate why the session event is not arriving.

Verify:
- correct event listener registration BEFORE FB.login()
- correct message origin validation
- correct message format parsing
- correct sessionInfoVersion
- correct Config ID
- correct Embedded Signup configuration
- correct event name
- correct handling of the popup/opener relationship
- correct timing
- no race condition
- no premature timeout
- no duplicate FB.login callbacks
- no second exchange of the same single-use code

Do not "fix" the timeout by simply increasing the timeout.

If the official Meta flow requires sessionInfoVersion 3 or another current version, implement the documented version exactly.

WABA/PHONE FLOW:

Once the session event is received, extract and log safely:

- waba_id
- phone_number_id
- business_id if provided

Then continue automatically through the official API sequence.

Do NOT ask the frontend user to manually enter WABA ID or Phone Number ID.

TOKEN:

Use the correct token type produced/required by the current Embedded Signup flow.

Do not assume that the OAuth authorization code itself is the final WhatsApp business token.

SUBSCRIBED_APPS:

After obtaining the correct business token and WABA/phone identifiers, execute the official subscribed_apps step and verify the response before continuing.

PHONE REGISTRATION:

Only call /register if the current official flow and onboarding state require it. Do not blindly register an already registered number.

WEBHOOK:

Verify that the WABA/app subscription and webhook configuration are correct, then verify that the webhook can receive WhatsApp events.

DATABASE:

Only save the integration after the required steps succeed.

The final successful state must be something equivalent to:

Embedded Signup opened
→ user completed Meta onboarding
→ authorization code received
→ session event received
→ WABA ID received
→ Phone Number ID received
→ correct token obtained
→ WABA subscribed_apps succeeded
→ phone registration completed if required
→ webhook connected/verified
→ integration saved
→ dashboard shows WhatsApp Connected

ERROR HANDLING:

For every Meta API call log:
- endpoint
- HTTP method
- status
- error code
- error subcode
- error message
- fbtrace_id

Never log:
- app secret
- access tokens
- authorization codes
- full personal/business data

Also prevent the same authorization code from being exchanged more than once.

TESTING:

After implementation:
1. run backend syntax/import checks
2. run frontend TypeScript/build checks
3. verify Config ID configuration
4. verify production frontend domain
5. perform a REAL browser Embedded Signup test
6. capture frontend console logs
7. capture backend logs
8. confirm the COMPLETE chain reaches "Connected"

Do not tell me "ready for testing" if only syntax checks pass.

The task is NOT complete until the real Embedded Signup flow reaches the connected state or the remaining blocker is proven to be a Meta Dashboard/configuration issue with exact evidence.

Finally, give me:
- files changed
- exact root cause
- exact Meta configuration required
- exact flow implemented
- tests performed
- final remaining blocker, if any