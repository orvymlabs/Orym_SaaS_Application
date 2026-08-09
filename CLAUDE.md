We now have the ACTUAL production Render logs. Do not make another blind code change.

IMPORTANT DISCOVERY:

The backend is ALREADY using:

GET https://graph.facebook.com/v26.0/oauth/access_token

with:

* client_id
* client_secret
* code

and `redirect_uri` is genuinely OMITTED.

Render confirms:

`redirect_uri included: False`

Meta still returns:

Error Code: 100
Error Subcode: 36008
Error Type: OAuthException

`Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request`

Therefore DO NOT simply remove redirect_uri from the backend again. It is already removed.

The current problem is now most likely related to the Embedded Signup authorization/configuration context or the exact redirect/domain configuration associated with the code.

==================================================
ACTUAL PRODUCTION FLOW
======================

Frontend:

https://apps.orvym.com

Meta App ID:

3862862217342382

Config ID:

2432311603846818

Graph API:

v26.0

Backend:

https://orym-saas-application.onrender.com

The frontend successfully:

* initializes Facebook SDK
* launches FB.login
* uses the Config ID
* completes Meta Embedded Signup
* receives a 451-character exchangeable code
* sends that code immediately to backend

Backend successfully receives the code.

The backend then performs:

GET /v26.0/oauth/access_token

with:

client_id
client_secret
code

NO redirect_uri.

Meta rejects the code with:

Error 100
Subcode 36008

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

==================================================
DO NOT CHANGE THE WORKING FRONTEND
==================================

Do NOT change:

* FB.login
* Config ID
* Facebook SDK initialization
* response_type
* Embedded Signup event listener
* existing authentication
* login
* signup
* dashboard
* unrelated APIs

==================================================
FIRST: VERIFY META CONFIGURATION
================================

Before changing backend code, inspect the Meta App configuration for:

1. Facebook Login for Business configuration

2. Embedded Signup configuration associated with:

   2432311603846818

3. Allowed Domains

4. Valid OAuth Redirect URIs

5. Client OAuth Login

6. Web OAuth Login

7. Login with JavaScript SDK

8. Enforce HTTPS

9. App Domains

10. Embedded Browser OAuth Login if required by the current Meta setup

11. Any configuration-specific redirect/domain settings

The production spawning domain is:

https://apps.orvym.com

Make sure Meta configuration is consistent with the production Embedded Signup flow.

Do not add random URLs.

Do not change the production URL.

Do not add the backend Render URL as an OAuth redirect unless Meta's current documentation specifically requires it for this exact flow.

==================================================
SECOND: VERIFY THE CODE IS NOT BEING REUSED
===========================================

The exchangeable Embedded Signup code is short-lived and single-use.

Make sure ORVYM is NOT exchanging the same code twice.

Check whether:

* frontend sends the request twice
* React Strict Mode causes duplicate handling
* FB.login callback fires more than once
* WA_EMBEDDED_SIGNUP event and FB.login callback both trigger the backend exchange
* backend retries the same code
* browser/network layer repeats the POST

There must be exactly ONE backend token-exchange attempt for each newly generated Embedded Signup code.

This is extremely important.

The Render logs currently show a fresh code and one exchange attempt, but verify the complete frontend/backend flow to ensure the same code is never exchanged twice.

==================================================
THIRD: VERIFY APP ID / CONFIG ID RELATIONSHIP
=============================================

Confirm that Config ID:

2432311603846818

belongs to App ID:

3862862217342382

and that the production frontend is launching the Embedded Signup configuration belonging to this exact Meta App.

Do not assume this.

Verify it in Meta Developer Dashboard.

==================================================
FOURTH: VERIFY GRAPH API VERSION
================================

The current backend uses:

v26.0

Confirm that the Embedded Signup configuration and current Meta documentation support this version.

Do not downgrade randomly.

Do not upgrade randomly.

Use the currently supported version for this app/flow.

==================================================
FIFTH: VERIFY APP SECRET
========================

Confirm the backend App Secret belongs to:

App ID 3862862217342382

Do not expose the secret.

Do not print it.

Do not change it unless it is actually incorrect.

==================================================
SIXTH: TEST WITH A FRESH CODE
=============================

After configuration/code fixes:

1. Open production.
2. Start Embedded Signup.
3. Complete the flow.
4. Generate a completely new exchangeable code.
5. Send it immediately.
6. Perform exactly ONE exchange.
7. Capture the actual Meta response.

Never manually reuse an old code.

==================================================
IMPORTANT
=========

Do NOT conclude that the solution is:

"add redirect_uri to the backend request."

The backend already omits redirect_uri.

Do NOT conclude that the solution is:

"remove redirect_uri from backend."

It is already removed.

The current task is to determine WHY Meta generated a code that Meta's `/oauth/access_token` endpoint refuses with subcode 36008.

Trace the complete relationship:

Meta App
→ Facebook Login for Business
→ Embedded Signup Configuration
→ production domain
→ FB.login
→ generated code
→ backend exchange

Find the mismatch.

==================================================
FINAL GOAL
==========

Do not stop at explaining the error.

Actually fix the underlying issue and make the production Embedded Signup work.

After the fix, verify:

Meta Embedded Signup
→ fresh code
→ ONE exchange
→ business token
→ WABA ID
→ phone number ID
→ existing ORVYM WhatsApp connection

Do not touch authentication, login, signup, or unrelated functionality.
