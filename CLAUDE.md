I want a permanent production-grade fix for our Meta WhatsApp Embedded Signup integration.

IMPORTANT:
The redirect_uri issue is already resolved.

Current production redirect_uri:
https://apps.orvym.com/dashboard/integrations/

Do NOT change the redirect_uri.
Do NOT change the App ID.
Do NOT change the Config ID.

App ID:
3862862217342382

Config ID:
2432311603846818

Frontend:
https://apps.orvym.com

Backend:
https://orym-saas-application.onrender.com

CURRENT PROBLEM:

Embedded Signup successfully completes and returns an exchangeable code.

The browser receives a WA_EMBEDDED_SIGNUP message event.

The current frontend logs show the code, but the backend eventually returns:

"No WhatsApp Business Account found. Complete WhatsApp Business setup and try again."

I do NOT want another workaround.

Implement the standard production Embedded Signup architecture:

Embedded Signup
→ session message
→ extract code + waba_id + phone_number_id + business_id
→ send all required values to backend
→ exchange code server-side
→ validate customer business token
→ use returned WABA ID directly
→ retrieve/validate phone number
→ subscribe WABA to app
→ save credentials
→ return successful connection to frontend.

STEP 1 — FRONTEND

Inspect the actual Embedded Signup message listener.

It must correctly parse:

type:
WA_EMBEDDED_SIGNUP

Successful event:
FINISH

And extract:

data.waba_id
data.phone_number_id
data.business_id

The expected successful structure is:

{
  data: {
    phone_number_id: "...",
    waba_id: "...",
    business_id: "..."
  },
  type: "WA_EMBEDDED_SIGNUP",
  event: "FINISH",
  version: 3
}

Do NOT rely only on the authorization code to discover the WABA.

The WABA ID and phone number ID returned by Embedded Signup are the source of truth.

Also handle:

event === "CANCEL"

and:

event === "ERROR"

without attempting onboarding.

STEP 2 — FRONTEND → BACKEND

Inspect the exact current request to:

POST /api/integrations/meta/oauth/callback

Change it so it sends:

{
  code,
  redirect_uri,
  waba_id,
  phone_number_id,
  business_id
}

Mask the code in logs.

Do NOT log access tokens or secrets.

STEP 3 — BACKEND

Inspect the callback request model/schema.

Add:

waba_id
phone_number_id
business_id

as appropriate.

Do not make them optional if they are required for the normal FINISH flow.

STEP 4 — CODE EXCHANGE

Exchange the short-lived Embedded Signup code server-side using the Meta OAuth token endpoint.

Use the exact redirect_uri:

https://apps.orvym.com/dashboard/integrations/

Do not introduce another redirect URI.

Log only safe metadata:
- exchange success/failure
- error code
- error subcode
- error message
- fbtrace_id

Never log:
- app secret
- client secret
- access token
- full authorization code

STEP 5 — WABA

DO NOT attempt to "guess" the WABA.

Use the waba_id returned by Embedded Signup.

Do NOT confuse:
- business_id
- WABA ID
- phone_number_id

They are separate IDs.

STEP 6 — PHONE NUMBER

Use:

GET /{WABA_ID}/phone_numbers

to validate/retrieve the customer's WhatsApp phone number.

Do NOT use:

/{object}?fields=phone_numbers

or any invalid phone_numbers field lookup.

Extract:

phone_number_id
display_phone_number
verified_name

and verify that it matches the phone_number_id returned by Embedded Signup.

STEP 7 — SUBSCRIBE WABA

After successful token exchange and WABA validation:

POST /{WABA_ID}/subscribed_apps

using the correct customer/business access token.

If this fails, return the REAL Meta error:

error.code
error.error_subcode
error.message
error.fbtrace_id

Do NOT replace it with:
"No WhatsApp Business Account found."

STEP 8 — DATABASE

After successful onboarding, save:

waba_id
phone_number_id
business_id
access_token
display_phone_number
verified_name
connection status

Never expose the access token to the frontend.

STEP 9 — ERROR HANDLING

Differentiate these cases:

1. Embedded Signup cancelled
2. Embedded Signup error
3. Authorization code exchange failed
4. Missing WABA ID
5. Invalid WABA ID
6. Phone number lookup failed
7. WABA subscription failed
8. Database save failed

Return useful errors for each case.

Do NOT use one generic:
"No WhatsApp Business Account found."

STEP 10 — VERIFY CURRENT PRODUCTION CODE

Inspect the actual source files before modifying anything.

Show me:
- current Embedded Signup listener
- current frontend callback request
- current backend request schema
- current OAuth exchange
- current WABA lookup
- current phone number lookup
- current subscribed_apps call

Then implement the fix.

STEP 11 — BUILD

After changes:

1. Build frontend successfully.
2. Verify generated production bundle contains the new WABA/phone_number/business_id handling.
3. Verify backend imports successfully.
4. Run tests if available.
5. Commit changes.
6. Deploy frontend and backend.

Do not claim completion until the production bundle contains the fix.

FINAL RESPONSE MUST SHOW:

1. Exact frontend event structure being parsed.
2. Exact fields extracted.
3. Exact frontend → backend request body, with code masked.
4. Exact Meta token endpoint.
5. Exact WABA phone_numbers endpoint.
6. Exact subscribed_apps endpoint.
7. Database fields saved.
8. Files changed.
9. Build result.
10. Deployment result.
11. Any Meta Dashboard setting actually required.

Most importantly:

DO NOT TRY ANOTHER REDIRECT_URI EXPERIMENT.

The permanent solution is to use the WABA ID and phone_number_id returned by Meta Embedded Signup and pass them to the backend, rather than trying to discover the WABA blindly after OAuth.