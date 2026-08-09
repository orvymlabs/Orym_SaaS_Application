I need you to DEBUG and FIX the existing Meta WhatsApp Embedded Signup implementation in our SaaS application.

IMPORTANT:
The Embedded Signup is ALREADY IMPLEMENTED.
Do NOT rebuild it.
Do NOT redesign the UI.
Do NOT create a new OAuth flow.
Do NOT replace the existing implementation.

The goal is simply to make the CURRENT implementation work correctly from start to finish.

CURRENT ISSUE:

The Meta/Facebook authorization popup opens successfully and the OAuth authorization code is being received, but the flow fails during the Meta OAuth/token exchange.

The exact error we are currently getting is:

Meta Error 36008

Fix this exact error.

EXPECTED EXISTING FLOW:

Connect WhatsApp
→ Meta WhatsApp Embedded Signup opens
→ User authorizes
→ WhatsApp onboarding continues
→ OAuth authorization code is generated
→ Frontend sends the code to our backend
→ Backend exchanges the code with Meta
→ Meta returns the required token/data
→ WABA / WhatsApp phone information is obtained
→ Connection is saved to the correct SaaS customer
→ WhatsApp is successfully connected.

DO NOT stop at the Facebook authorization popup. The COMPLETE existing Embedded Signup flow must work.

DEBUG THE EXISTING CODEBASE FIRST.

Check the frontend:

- Meta/Facebook SDK initialization
- Meta App ID
- Embedded Signup Config ID
- FB.login() configuration
- response_type
- override_default_response_type
- WA_EMBEDDED_SIGNUP event listener
- OAuth authorization code handling
- duplicate FB.login() calls
- duplicate event listeners
- duplicate API requests
- whether the authorization code is being sent to the backend more than once

Check the backend:

- OAuth authorization-code endpoint
- Meta token exchange request
- client_id
- client_secret
- redirect_uri
- Graph API version
- request parameters
- response handling
- error handling
- whether the same authorization code is being exchanged more than once

Check Meta configuration:

- Meta App ID and Embedded Signup Config ID belong to the same Meta App
- Embedded Signup configuration
- OAuth redirect configuration
- App domains
- required permissions
- WhatsApp Business configuration

VERY IMPORTANT:

The OAuth authorization code is single-use.

Make sure ONE user signup produces:
- exactly ONE authorization code
- exactly ONE backend request
- exactly ONE Meta code exchange

Do not exchange the same code twice.

Do not randomly change the redirect_uri.
Do not randomly change the Graph API version.
Do not create another OAuth flow.
Do not mock a successful response.
Do not hide or suppress error 36008.

FIRST:
Inspect the current implementation and identify the EXACT root cause of Meta error 36008.

THEN:
Make only the necessary changes to fix the existing implementation.

AFTER FIXING:
Test the complete existing flow:

Connect WhatsApp
→ Meta Embedded Signup
→ Authorization
→ WhatsApp onboarding
→ OAuth code
→ Backend
→ Meta token exchange
→ WABA / Phone Number information
→ Save connection
→ Successful WhatsApp connection.

Also explain to me:
1. What was causing error 36008?
2. Which file(s) you changed?
3. What exactly you changed?
4. Why the change fixes the error?
5. Confirm that the existing Embedded Signup implementation was preserved and not rebuilt.