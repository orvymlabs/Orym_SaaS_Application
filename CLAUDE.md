You are working on ORVYM, a production multi-tenant SaaS platform that allows each customer/tenant to connect their own WhatsApp Business Account through Meta WhatsApp Embedded Signup.

IMPORTANT:
Do NOT give me a theoretical answer.
Do NOT just explain the issue.
Inspect the actual repository, existing frontend implementation, backend implementation, environment variables, API routes, and production build configuration.

Your job is to IMPLEMENT and VERIFY a permanent production-ready solution.

==================================================
CURRENT PRODUCTION CONFIGURATION
==================================================

Frontend:
https://apps.orvym.com

Backend:
https://orym-saas-application.onrender.com

Meta App ID:
3862862217342382

Meta Embedded Signup Config ID:
2432311603846818

Current production redirect URI:
https://apps.orvym.com/dashboard/integrations/

DO NOT change these values unless Meta's current official documentation proves that a change is required.

The redirect URI currently being sent by the frontend is:

https://apps.orvym.com/dashboard/integrations/

The same exact value, including the trailing slash, must be used consistently wherever Meta requires redirect_uri.

==================================================
CURRENT PROBLEM
==================================================

The Embedded Signup popup successfully opens.

Meta successfully returns an exchangeable authorization code.

Example production logs:

"Exchangeable token code received (length: 451)"

Then frontend sends:

POST
https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback

Current frontend logs:

redirect_uri:
https://apps.orvym.com/dashboard/integrations/

BUT the latest implementation is showing:

waba_id: undefined
phone_number_id: undefined
business_id: undefined

and backend returns:

422 Unprocessable Entity

Previous versions had:

400
"No WhatsApp Business Account found. Complete WhatsApp Business setup and try again."

There were also previous errors:

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

and:

"Can't load URL: The domain of this URL isn't included in the app's domains."

The redirect URI issue has now been corrected and Meta is returning the exchangeable code.

DO NOT go backwards and start randomly changing redirect_uri again.

The current problem is the Embedded Signup completion data / WABA identification / backend exchange and onboarding flow.

==================================================
IMPORTANT META EMBEDDED SIGNUP REQUIREMENT
==================================================

Implement the standard Meta WhatsApp Embedded Signup flow according to Meta's CURRENT official documentation.

Do not invent a custom OAuth flow.

Do not assume that waba_id, phone_number_id, or business_id will magically be returned by FB.login() directly.

The implementation must correctly process the Embedded Signup completion message/event.

The flow must support:

1. User clicks "Connect WhatsApp"
2. Facebook SDK is initialized
3. Embedded Signup opens using Config ID
4. Meta completes onboarding
5. Meta sends the Embedded Signup completion event/message
6. Frontend extracts:
   - exchangeable code
   - waba_id
   - phone_number_id
   - business_id
7. Frontend immediately sends all required data to backend
8. Backend exchanges the temporary code server-side
9. Backend obtains/validates the resulting access token
10. Backend validates the WABA
11. Backend validates the phone number
12. Backend subscribes the WABA/app if required
13. Backend stores the WhatsApp connection against THE CURRENT LOGGED-IN TENANT
14. Frontend receives success
15. UI shows the connected WhatsApp Business account/number
16. The tenant can then use WhatsApp messaging through ORVYM

==================================================
STEP 1 — INSPECT THE EXISTING CODE FIRST
==================================================

Before modifying anything, inspect:

- Meta WhatsApp integration frontend component/page
- FB.login implementation
- Facebook SDK initialization
- postMessage/event listener
- Embedded Signup completion handling
- OAuth callback API call
- backend OAuth callback route
- backend Meta service/helper
- database models
- tenant/user authentication
- existing WhatsApp integration model
- environment variables
- API schemas / Pydantic models if backend is FastAPI
- production build configuration

Search the entire repository for:

- FB.login
- config_id
- 2432311603846818
- response_type
- override_default_response_type
- redirect_uri
- WA_EMBEDDED_SIGNUP
- postMessage
- waba_id
- phone_number_id
- business_id
- oauth/access_token
- subscribed_apps
- phone_numbers
- WhatsAppBusinessAccount
- Meta
- Facebook

Do not create duplicate integration logic if an existing implementation already exists.

Fix the existing implementation cleanly.

==================================================
STEP 2 — EMBEDDED SIGNUP FRONTEND
==================================================

Use the Meta Embedded Signup configuration:

config_id:
2432311603846818

The FB.login Embedded Signup invocation must be consistent with Meta's current documentation.

Do NOT add arbitrary OAuth parameters.

Do NOT use a separate redirect-based OAuth flow.

Do NOT remove the Embedded Signup flow.

Use the exchangeable code returned by Embedded Signup.

The implementation must correctly listen for the Meta Embedded Signup completion message.

Handle both possible message representations safely if necessary:

- JSON/object event data
- URL/query-string style event data

The current production browser log looks similar to:

cb=...
domain=apps.orvym.com
is_canvas=false
origin=https://apps.orvym.com/...
relation=opener
frame=...
code=...
base_domain=apps.orvym.com
enforce_https=1

The implementation must parse this correctly.

Do NOT parse only the code and discard the other onboarding information.

The completion payload must be inspected for the standard Embedded Signup finish information, including:

- code
- waba_id
- phone_number_id
- business_id

If Meta provides these values inside a nested structure, correctly extract them.

If the implementation receives a `WA_EMBEDDED_SIGNUP` event, explicitly handle that event.

Log safely:

Embedded Signup completed
code received: yes
waba_id: <value>
phone_number_id: <value>
business_id: <value>

NEVER log:

- access_token
- client_secret
- full authorization code
- other credentials

Only log safe metadata such as code length and IDs.

==================================================
STEP 3 — REDIRECT URI
==================================================

Use exactly:

https://apps.orvym.com/dashboard/integrations/

Do not silently generate another URL.

Do not use:

http://localhost
https://orym-saas-application.onrender.com
https://apps.orvym.com/dashboard/integrations
or any other variant

when the configured production redirect URI requires the trailing slash.

Centralize the redirect URI in one configuration value.

For production:

META_REDIRECT_URI =
https://apps.orvym.com/dashboard/integrations/

The same exact string must be used for:

- authorization configuration where applicable
- frontend request
- backend OAuth token exchange
- Meta App configuration

Do not append/remove "/" automatically.

==================================================
STEP 4 — FRONTEND → BACKEND REQUEST
==================================================

Inspect the existing frontend request.

It must send all required data.

The request should conceptually contain:

{
  "code": "<exchangeable_code>",
  "redirect_uri": "https://apps.orvym.com/dashboard/integrations/",
  "waba_id": "<actual_waba_id>",
  "phone_number_id": "<actual_phone_number_id>",
  "business_id": "<actual_business_id>"
}

Use the exact existing backend schema if different, but make frontend and backend schemas match exactly.

Do NOT send:

waba_id: undefined

phone_number_id: undefined

business_id: undefined

If those values are missing from the completion event, DO NOT send a broken request.

Instead:

1. inspect the exact Meta event payload
2. determine where the values are located
3. parse them correctly
4. only then call the backend

The code expires quickly, so do not introduce unnecessary delays.

==================================================
STEP 5 — BACKEND CALLBACK
==================================================

Inspect:

POST /api/integrations/meta/oauth/callback

Make the request schema explicit and robust.

The endpoint must validate:

- code
- redirect_uri
- waba_id
- phone_number_id
- business_id

Do not return generic:

[object Object]

errors.

Return structured useful errors such as:

{
  "detail": "Missing waba_id from Embedded Signup completion data"
}

or:

{
  "detail": "Meta token exchange failed",
  "meta_error": "..."
}

Do not expose client_secret or access tokens.

==================================================
STEP 6 — SERVER-SIDE META CODE EXCHANGE
==================================================

The temporary Embedded Signup code must be exchanged SERVER-SIDE.

Do not exchange the Meta client secret in the browser.

Backend should use:

- Meta App ID
- Meta App Secret
- exchangeable code
- exact redirect_uri required by Meta

Call Meta's current OAuth/token endpoint according to the current official documentation.

Conceptually:

GET/POST to Meta Graph API OAuth token endpoint

with:

client_id=<META_APP_ID>
client_secret=<META_APP_SECRET>
code=<exchangeable_code>
redirect_uri=https://apps.orvym.com/dashboard/integrations/

IMPORTANT:

Do not blindly omit redirect_uri.

Do not blindly send an empty string.

Do not blindly send a different URL.

Use the exact redirect_uri behavior required by Meta's CURRENT Embedded Signup documentation and ensure it is identical to the URI associated with the authorization/code flow.

Inspect Meta's actual response.

Do not assume success.

==================================================
STEP 7 — WABA VALIDATION
==================================================

After successful code exchange, use the resulting access token server-side.

Validate the WABA returned by Embedded Signup.

Use:

GET /{waba_id}

and request only fields that are actually supported by the current Graph API version.

Then retrieve phone numbers using:

GET /{waba_id}/phone_numbers

Do NOT request:

phone_numbers

from an invalid/nonexistent object field.

The previous error:

(#100) Tried accessing nonexisting field (phone_numbers)

must NOT happen again.

Use the correct `/phone_numbers` edge.

Verify that the supplied:

phone_number_id

actually belongs to:

waba_id

If validation fails, return a clear error.

==================================================
STEP 8 — BUSINESS VALIDATION
==================================================

If business_id is provided by Embedded Signup:

validate it where appropriate.

Do not assume the WABA is automatically associated with the expected business.

Do not invent a business ID.

Use the actual ID returned by Meta.

==================================================
STEP 9 — SUBSCRIBE THE WABA
==================================================

After validating the WABA, implement the required Meta subscription step according to current Embedded Signup documentation.

Use the correct WABA endpoint, conceptually:

POST /{waba_id}/subscribed_apps

using the appropriate access token.

Verify the response.

Do not mark the integration as connected if subscription fails when subscription is required.

==================================================
STEP 10 — MULTI-TENANT ORVYM REQUIREMENT
==================================================

THIS IS CRITICAL.

ORVYM is a SaaS platform.

Every customer can connect their OWN:

- Meta Business
- WABA
- WhatsApp phone number

The connection MUST be associated with the currently authenticated ORVYM tenant/user.

Do NOT store one global WhatsApp credential.

Do NOT overwrite another tenant's WhatsApp account.

Use the existing authenticated user/tenant context.

The final database record should conceptually contain:

tenant_id
business_id
waba_id
phone_number_id
phone_number
display_name if available
access_token (securely stored)
token metadata if needed
status
connected_at
updated_at

Follow the existing database architecture instead of creating duplicate tables.

If an existing WhatsApp integration model exists, extend/fix it rather than creating unnecessary duplicate models.

==================================================
STEP 11 — TOKEN SECURITY
==================================================

NEVER expose Meta access tokens to the browser.

NEVER log access tokens.

NEVER log App Secret.

NEVER return App Secret from the backend.

Store credentials server-side only.

If the project already has encryption/secret storage, use it.

==================================================
STEP 12 — IDEMPOTENCY
==================================================

The user may complete Embedded Signup more than once.

The backend should safely handle reconnect/retry.

If the same tenant connects the same WABA/phone again:

- update the existing connection
- do not create duplicate records

If the tenant connects a different WABA/number:

- correctly create/update the tenant's connection according to existing ORVYM architecture

==================================================
STEP 13 — FRONTEND SUCCESS FLOW
==================================================

After backend successfully completes:

- token exchange
- WABA validation
- phone validation
- subscription
- database save

return a clear success response.

Frontend should then:

- refresh integration state
- display connected WhatsApp Business information
- stop showing "Connect WhatsApp"
- show connected status
- show the connected phone/business information safely

Do not show access tokens.

==================================================
STEP 14 — ERROR HANDLING
==================================================

Replace vague errors such as:

"[object Object]"

with structured errors.

Handle separately:

1. Meta SDK initialization failure
2. Embedded Signup cancellation
3. Missing code
4. Missing waba_id
5. Missing phone_number_id
6. Missing business_id
7. Token exchange failure
8. Invalid redirect URI
9. WABA lookup failure
10. phone_numbers lookup failure
11. phone number mismatch
12. subscribed_apps failure
13. database failure
14. authentication/tenant failure

The frontend should show the actual useful reason.

==================================================
STEP 15 — META CONFIGURATION
==================================================

Inspect the actual Meta App configuration required by the current Embedded Signup implementation.

Do NOT tell me to randomly add domains.

Determine the exact URLs actually used by the implementation.

For the current production setup, verify:

App Domains:
apps.orvym.com

OAuth Redirect URI:
https://apps.orvym.com/dashboard/integrations/

Do not add:

orym-saas-application.onrender.com

unless the actual Meta OAuth flow proves that URL is being used as a browser redirect URI.

The backend domain is an API server, not automatically an OAuth browser redirect URI.

==================================================
STEP 16 — CURRENT META DOCUMENTATION
==================================================

Before finalizing the implementation, check Meta's CURRENT official WhatsApp Embedded Signup documentation.

Do NOT rely on old blog posts, Stack Overflow answers, random GitHub implementations, or assumptions.

Verify:

- current Embedded Signup JS flow
- current Config ID usage
- response_type behavior
- exchangeable code behavior
- completion event/message format
- waba_id extraction
- phone_number_id extraction
- business_id extraction
- token exchange requirements
- redirect_uri requirements
- WABA subscription requirements
- current Graph API endpoint/version

If the current official Meta documentation differs from an assumption in this prompt, follow Meta's current documentation and explain the exact difference.

==================================================
STEP 17 — BUILD VERIFICATION
==================================================

After implementation:

1. Run frontend lint/typecheck if available.
2. Run backend tests/typecheck if available.
3. Build the frontend production bundle.
4. Search the generated production bundle for the new Embedded Signup implementation.
5. Confirm the old broken logic is NOT present.

Specifically search the production build for old logs such as:

"waba_id: undefined"
"phone_number_id: undefined"
"business_id: undefined"

and old incorrect redirect behavior.

Verify that the production bundle contains the corrected extraction and request logic.

Do not say "fixed" unless the production build actually contains the changes.

==================================================
STEP 18 — ADD DEBUG LOGGING FOR ONE TEST
==================================================

Add safe temporary/debug logging around:

Embedded Signup event received
event type
available payload keys
code received: yes/no
waba_id
phone_number_id
business_id
backend request started
Meta token exchange started
Meta token exchange succeeded/failed
WABA validation succeeded/failed
phone validation succeeded/failed
subscription succeeded/failed
database save succeeded/failed

Never log secrets.

==================================================
FINAL ACCEPTANCE CRITERIA
==================================================

The implementation is considered COMPLETE only if this exact flow works:

ORVYM user
↓
Dashboard
↓
Integrations
↓
Connect WhatsApp
↓
Meta Embedded Signup opens
↓
Customer completes their own Meta Business/WABA/WhatsApp onboarding
↓
Meta returns exchangeable code
↓
Frontend receives Embedded Signup completion event
↓
Frontend correctly extracts:
  code
  waba_id
  phone_number_id
  business_id
↓
Frontend sends all required values to backend
↓
Backend exchanges code with Meta
↓
Backend validates WABA
↓
Backend retrieves phone numbers
↓
Backend validates phone_number_id
↓
Backend subscribes WABA/app if required
↓
Backend saves credentials against CURRENT ORVYM TENANT
↓
Frontend receives success
↓
WhatsApp integration shows CONNECTED

There must be NO:

- undefined waba_id
- undefined phone_number_id
- undefined business_id
- 422 caused by missing Embedded Signup fields
- redirect_uri mismatch
- empty redirect_uri workaround
- "(#100) Tried accessing nonexisting field (phone_numbers)"
- "No WhatsApp Business Account found" caused by incorrect extraction
- [object Object]
- global/shared tenant credentials

==================================================
FINAL REPORT REQUIRED
==================================================

After making the changes, report:

1. Exact frontend FB.login configuration used
2. Exact Embedded Signup completion event format detected
3. Exact fields extracted from Meta
4. Exact frontend → backend request body/schema
5. Exact production redirect_uri
6. Exact Meta OAuth/token endpoint
7. Exact backend → Meta token exchange parameters
   (DO NOT reveal secret values)
8. Exact WABA endpoint used
9. Exact phone number endpoint used
10. Exact WABA subscription endpoint used
11. Exact database model/table used
12. How tenant isolation is guaranteed
13. Exact Meta App Domain required
14. Exact OAuth Redirect URI required
15. Files changed
16. Tests/build commands executed
17. Production bundle verification result
18. Any remaining issue, if and ONLY if something genuinely cannot be verified

MOST IMPORTANT:

Do not keep patching the same error blindly.

Trace the complete Embedded Signup data flow from:

Meta
→ browser event
→ frontend parser
→ frontend API request
→ backend schema
→ Meta token exchange
→ WABA lookup
→ phone lookup
→ WABA subscription
→ tenant database
→ frontend success state.

The goal is not merely to remove the current 422.

The goal is to make ORVYM's production WhatsApp Embedded Signup a complete, reusable, multi-tenant SaaS onboarding flow that works for real customers.