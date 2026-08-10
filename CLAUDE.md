I need you to properly fix the existing Meta WhatsApp Embedded Signup integration in my SaaS application.

DO NOT rebuild the integration from scratch.
DO NOT change unrelated application functionality.
DO NOT hide errors.
DO NOT use fake/mock WABA IDs.
DO NOT blindly add random permissions.

The OAuth/token exchange is already WORKING and must remain untouched.

CURRENT SUCCESSFUL FLOW:

Embedded Signup
→ OAuth code received
→ backend receives code
→ Meta /oauth/access_token
→ HTTP 200
→ access token received

Production log confirms:

Status Code: 200
Access token received: YES
Token exchange successful

So DO NOT modify the successful token exchange logic unless your investigation proves it is required.

==================================================
PROBLEM 1 — WABA DISCOVERY IS WRONG
==================================================

After successful token exchange, the backend currently does:

GET
https://graph.facebook.com/v26.0/me/businesses
fields=id,name

This returns:

(#100) Missing Permission

The backend then returns:

HTTP 400
(#100) Missing Permission

The current code is trying to discover the WABA through /me/businesses.

I need you to inspect the existing Meta WhatsApp Embedded Signup implementation and implement the CORRECT WABA discovery flow for Embedded Signup.

Do NOT simply add a random permission to make /me/businesses work.

First inspect the complete flow:

FRONTEND:
- FB.login()
- config_id
- response_type
- override_default_response_type
- extras
- WA_EMBEDDED_SIGNUP postMessage listener
- OAuth redirect-back handling
- state/code handling
- callback request

BACKEND:
- /api/integrations/meta/oauth/callback
- token exchange
- WABA discovery
- phone number discovery
- business ID resolution
- final WhatsApp connection save

Determine exactly where the WABA ID and phone_number_id are supposed to come from in this Embedded Signup flow.

If Meta provides the WABA ID / phone number ID through the Embedded Signup completion event, capture those values on the frontend and send them securely to the backend.

The frontend currently logs:

waba_id: not provided - backend will resolve
phone_number_id: not provided - backend will resolve
business_id: not provided - backend will resolve

This must be fixed.

Do not leave these values empty if the Embedded Signup event provides them.

Inspect the actual postMessage event payload received from Meta.

Add safe diagnostic logging that shows the EVENT TYPE and NON-SENSITIVE ID fields only.

Never log:
- access tokens
- client secrets
- OAuth codes
- authorization headers

The backend request should contain the actual IDs when available.

Expected data flow:

Meta Embedded Signup
→ completion event
→ extract real WABA ID
→ extract real Phone Number ID
→ extract business ID if available
→ OAuth code
→ backend
→ token exchange
→ validate/access the supplied WABA
→ get/verify phone number
→ save WhatsApp integration

==================================================
PROBLEM 2 — PERMISSIONS
==================================================

Inspect the Meta App configuration and Embedded Signup configuration used by this application.

Verify the exact permissions/scopes requested by the Embedded Signup configuration and the permissions actually present on the returned access token.

Do not assume that /me/businesses is the correct endpoint.

Use the correct Meta-supported WhatsApp Business / Embedded Signup Graph API flow for the WABA and phone number IDs obtained from Embedded Signup.

If a specific permission is genuinely required for the API operation we actually need, identify it explicitly and update the implementation/configuration accordingly.

Do not add unrelated permissions.

The final implementation must work with the access token actually returned by Embedded Signup.

==================================================
PROBLEM 3 — POPUP / WINDOW BEHAVIOR
==================================================

The current Meta Embedded Signup opens as a large/full-page browser-style experience.

I want it to behave as a proper Meta Embedded Signup popup/window:

User clicks:
"Connect WhatsApp"

→ Meta Embedded Signup opens in a centered popup/window
→ SaaS page stays open behind it
→ user completes Meta WhatsApp onboarding
→ result is returned to the SaaS application
→ popup closes/returns
→ integration becomes connected

Inspect the current FB.login implementation and determine why it is opening as a full-page experience.

Do NOT create a fake popup with an iframe.
Do NOT recreate Meta's UI.
Do NOT use an iframe to bypass Meta's OAuth restrictions.

Use the official supported Meta/Facebook Login + Embedded Signup popup flow.

Preserve:
- config_id
- response_type
- override_default_response_type
- extras
- OAuth callback handling
- postMessage handling

Only change the launch mechanism/configuration required for the correct popup behavior.

If the current implementation uses a redirect URI that causes the whole browser page to navigate, correct the flow while preserving the already-working OAuth exchange.

==================================================
PROBLEM 4 — PREVENT DUPLICATE CALLBACKS
==================================================

Ensure one user click results in:

ONE Embedded Signup session
ONE OAuth code
ONE backend callback
ONE token exchange

Prevent duplicate:
- FB.login calls
- message listeners
- OAuth callback requests
- token exchanges

The OAuth exchangeable code expires quickly, so do not retry the same code multiple times.

==================================================
IMPORTANT — DO NOT BREAK EXISTING SYSTEM
==================================================

Do not modify:
- authentication
- dashboard
- billing
- existing WhatsApp bot functionality
- unrelated integrations
- database tables unrelated to Meta integration
- existing UI outside the Connect WhatsApp flow

Make the smallest safe changes required.

==================================================
DEBUGGING REQUIREMENT
==================================================

Before changing the code, inspect the current implementation and tell me:

1. Exact source of the WABA ID in the current Embedded Signup flow
2. Exact source of phone_number_id
3. Why frontend currently sends:
   waba_id: not provided
   phone_number_id: not provided
4. Why backend falls back to /me/businesses
5. Why /me/businesses returns Missing Permission
6. What exact API/edge should be used instead
7. Why the current launch opens full-page instead of popup
8. Which exact frontend/backend files/functions will be modified

Then implement the fix.

==================================================
FINAL ACCEPTANCE TEST
==================================================

Do not consider the task complete until this flow works:

1. Open SaaS dashboard
2. Click Connect WhatsApp
3. Small centered Meta Embedded Signup popup/window opens
4. Complete Meta WhatsApp Business setup
5. Real WABA ID is captured
6. Real Phone Number ID is captured
7. OAuth code is received
8. Backend receives code + required IDs
9. Meta token exchange returns HTTP 200
10. No /me/businesses Missing Permission error
11. WABA is successfully verified/accessed
12. Phone number is successfully verified/accessed
13. WhatsApp integration is saved to the correct user
14. Popup closes/returns to SaaS
15. UI shows WhatsApp as connected

If any step fails, inspect the actual Meta response and fix the root cause instead of suppressing the error.