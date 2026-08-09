We now have detailed production logs. DO NOT rebuild the existing implementation.

The previous OAuth/token exchange problem is FIXED.

The logs prove:

Step 1/5 - Meta token exchange started
→ Meta returned HTTP 200
→ Access token received: YES
→ Token exchange successful

So DO NOT modify the successful token exchange unless absolutely necessary.

The CURRENT failure is specifically WABA discovery.

Production logs:

Step 2/5 - No WABA ID supplied, discovering via debug_token

debug_token response:
- Debug token OK
- granular scopes found
- WABA IDs identified: []

Then:
"No WABA IDs found in debug_token granular_scopes"

And the backend returns:

HTTP 400:
"No WhatsApp Business Account found. Complete WhatsApp Business setup and try again."

Frontend logs also show:

waba_id: not provided - backend will resolve
phone_number_id: not provided - backend will resolve
business_id: not provided - backend will resolve

THIS IS THE ISSUE TO FIX.

Do not rebuild Meta Embedded Signup.
Do not redesign the UI.
Do not change unrelated SaaS functionality.
Do not change the already-working OAuth token exchange.

Inspect the existing Embedded Signup event handling and determine why the WhatsApp Business information is not being captured.

Specifically inspect:

1. WA_EMBEDDED_SIGNUP postMessage listener
2. The exact event payload received after Embedded Signup
3. How the frontend extracts:
   - waba_id
   - phone_number_id
   - business_id
4. Whether the event listener is registered before FB.login()
5. Whether the listener is filtering the wrong event name
6. Whether the listener is reading the wrong payload structure
7. Whether the Meta event contains the WABA/phone information under a different field
8. Whether the values are lost during the OAuth redirect-back
9. Whether the OAuth callback is being processed before the Embedded Signup completion event
10. The exact JSON payload sent from frontend to:
   POST /api/integrations/meta/oauth/callback

IMPORTANT:

The current backend fallback:

"No WABA ID supplied → discover via debug_token"

is failing because debug_token returns:

WABA IDs identified: []

Do not simply suppress this error.

Do not fabricate a WABA ID.

Do not use a fake phone number ID.

Find the correct Meta-supported source for the WABA/phone information produced by the existing Embedded Signup flow.

If the Embedded Signup completion event provides the IDs, capture them and send them to the backend.

If the IDs are supposed to be obtained server-side after the successful token exchange, implement the correct Meta API request/edge for the current Embedded Signup flow rather than relying on debug_token granular_scopes.

The successful Step 1 token exchange must remain intact.

Desired flow:

Embedded Signup
→ user completes WhatsApp setup
→ capture the correct WABA/phone/business information
→ OAuth code received
→ token exchange succeeds (already working)
→ identify WABA
→ identify phone number
→ save connection
→ successful WhatsApp integration.

Before changing code, show me:
- the exact current event payload received from Meta (with tokens/secrets redacted)
- the exact frontend callback payload
- why waba_id is currently missing
- why debug_token returns an empty WABA list

Then make the minimum required fix.

Do not modify unrelated application functionality.