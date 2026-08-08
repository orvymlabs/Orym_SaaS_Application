Fix ONLY the WhatsApp Embedded Signup integration.

This is a very strict targeted change.

## DO NOT TOUCH ANYTHING ELSE

ABSOLUTELY DO NOT MODIFY, REFACTOR, REMOVE, OR REBUILD:

* Authentication
* Login
* Signup / Registration
* User accounts
* Sessions
* Authorization
* Existing dashboard
* Existing APIs unrelated to Embedded Signup
* Existing database
* Existing user/tenant logic
* Existing application logic
* Any other integration
* Any existing working functionality

Everything outside WhatsApp Embedded Signup must remain exactly as it is.

DO NOT change authentication or signup/login under any circumstances.

## ONLY CHANGE THIS

Remove the CURRENT WhatsApp Embedded Signup implementation and rebuild ONLY that specific integration according to the CURRENT official Meta WhatsApp Embedded Signup documentation.

The replacement must be isolated to the WhatsApp Embedded Signup code.

Do not rebuild the whole OAuth/authentication system.

Do not replace the application's existing authentication.

Do not create a new login system.

Do not modify the existing signup/login flow.

## CURRENT META DETAILS

App ID:

3862862217342382

Config ID:

2432311603846818

Production frontend:

https://apps.orvym.com

Production backend:

https://orym-saas-application.onrender.com

Keep the existing App ID and Config ID unless the current official Meta documentation proves that a change is required.

## CURRENT EMBEDDED SIGNUP STATUS

The current implementation successfully:

* initializes Facebook SDK
* launches Embedded Signup
* receives Meta's SDK_QUERY_STRING event
* receives the exchangeable authorization code

The payload contains:

["cb","domain","is_canvas","origin","relation","frame","code","base_domain"]

The exchangeable code is successfully received with length around 451.

The old implementation then fails with:

HTTP 400

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

## REQUIRED APPROACH

Use the CURRENT official Meta WhatsApp Embedded Signup documentation as the source of truth.

Choose the simplest officially supported Embedded Signup implementation.

Do not continue patching the old implementation if it is based on outdated/custom OAuth logic.

Remove only the old Embedded Signup-specific implementation and replace it with the current documented approach.

## IMPORTANT

Do NOT try to integrate Embedded Signup with the application's login/signup/authentication system.

The user is already authenticated in ORVYM.

Embedded Signup is ONLY for connecting the user's WhatsApp Business account.

The existing ORVYM authentication must remain completely untouched.

The flow should simply be:

Existing logged-in ORVYM user
↓
Existing "Connect WhatsApp" action
↓
WhatsApp Embedded Signup
↓
Meta authorization
↓
Exchangeable code
↓
Existing/required backend Embedded Signup processing
↓
WhatsApp connection completed

Do NOT create or modify any login/signup/authentication flow.

## REDIRECT URI

Investigate the current redirect_uri error using the current official Meta documentation.

Do not automatically keep the old redirect_uri implementation.

Determine whether the current Embedded Signup flow actually requires the old OAuth redirect_uri validation.

If it does not, remove ONLY that obsolete Embedded Signup redirect handling.

If it does require a redirect URI, configure it exactly according to Meta's current documentation.

Do not modify application authentication redirects.

Do not modify login/signup redirects.

Do not modify existing auth callbacks.

Any redirect change must be isolated strictly to WhatsApp Embedded Signup.

## FRONTEND

Rebuild only the Embedded Signup component/handler.

It must:

* initialize/use Facebook SDK correctly
* launch Embedded Signup once
* use the existing Config ID
* receive the exchangeable code
* process the code once
* communicate with the Embedded Signup backend endpoint
* handle success
* handle cancellation
* handle errors
* allow retry

Do not modify authentication-related components.

## BACKEND

Modify ONLY backend code directly responsible for WhatsApp Embedded Signup processing.

Do not modify authentication middleware.

Do not modify login endpoints.

Do not modify signup endpoints.

Do not modify session handling.

Do not modify user authentication.

Do not create a new authentication system.

Use the currently authenticated ORVYM user through the EXISTING authentication mechanism without changing that mechanism.

The backend should securely process the Meta Embedded Signup authorization code according to the current official Meta documentation.

Do not expose App Secret or access tokens.

## DUPLICATE LAUNCH

Fix duplicate Embedded Signup execution if present.

Required:

ONE CLICK
→ ONE FB.login()
→ ONE EMBEDDED SIGNUP
→ ONE CODE
→ ONE BACKEND REQUEST

Do not affect any other buttons or authentication actions.

## ACCOUNT INFORMATION

Do not assume WABA ID, phone number ID, or business ID are present in SDK_QUERY_STRING.

Follow the current Meta Embedded Signup documentation to obtain the required information after processing the exchangeable code.

Do not hardcode IDs.

Do not fabricate IDs.

## STRICT ISOLATION RULE

Before changing any file, identify whether it belongs to:

A. Authentication/Login/Signup
B. WhatsApp Embedded Signup

If it belongs to A:
DO NOT CHANGE IT.

If it belongs specifically to B:
You may change it.

If a file contains both systems:
make the smallest possible isolated change only to the Embedded Signup section.

Do not refactor the file.

## SUCCESS CONDITION

The final result must be:

User logs into ORVYM using the EXISTING login system
→ opens existing dashboard
→ clicks Connect WhatsApp
→ Embedded Signup opens
→ Meta onboarding completes
→ exchangeable code is received
→ backend processes it correctly
→ WhatsApp connection succeeds

The existing login/signup/authentication must work exactly as before.

## FINAL VERIFICATION

Before finishing, verify:

[ ] Existing login still works
[ ] Existing signup still works
[ ] Existing authentication still works
[ ] Embedded Signup launches
[ ] Embedded Signup launches only once
[ ] Exchangeable code is received
[ ] Code is processed once
[ ] Backend Embedded Signup processing succeeds
[ ] No redirect_uri mismatch
[ ] WhatsApp connection completes
[ ] No unrelated files/functionality were modified

## FINAL REPORT

Report only:

1. Embedded Signup root cause
2. Embedded Signup files changed
3. What was removed
4. What was rebuilt
5. Meta documentation approach used
6. Redirect URI handling
7. Test result
8. Confirmation that LOGIN, SIGNUP, AUTHENTICATION and all unrelated functionality were NOT modified

DO NOT TOUCH AUTH, LOGIN, SIGNUP, OR ANY OTHER PART OF THE APPLICATION.
