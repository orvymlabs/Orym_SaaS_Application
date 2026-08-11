DO NOT rely on Git history for this fix. The previous working commit may not exist in Git.

We have PRODUCTION LOG EVIDENCE of the previously working behavior, so reconstruct the working behavior from the logs and current code.

IMPORTANT REGRESSION:

Previously the Meta WhatsApp Embedded Signup OAuth token exchange SUCCESSFULLY worked.

Historical production log evidence:

[EmbeddedSignup] Step 1/5 - Meta token exchange started

META GRAPH API RESPONSE:
Status Code: 200
Access token received: YES
Token exchange successful

Then:

[EmbeddedSignup] Step 2/5 - No WABA ID supplied, discovering via business portfolio edges

The failure at that time was ONLY:
(#100) Missing Permission

Therefore DO NOT treat OAuth token exchange as a new problem to solve from scratch.

CURRENT regression:

[EmbeddedSignup] Step 1/6 - Meta token exchange started

Meta response:
Status Code: 400
Error code: 100
Error subcode: 36008
OAuthException

Error:
"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

CURRENT FACTS:

App ID:
3862862217342382

Config ID:
2432311603846818

Frontend:
https://apps.orvym.com/dashboard/integrations/

Frontend successfully receives:
LOGIN_CODE_RECEIVED (length: 451)

Backend successfully receives the fresh OAuth code.

The failure happens only during Meta access-token exchange.

TASK:

1. Inspect the CURRENT frontend and backend implementation completely.

2. Find every place where redirect_uri is:
   - defined
   - generated
   - passed to FB.login
   - passed to the backend
   - passed to Meta /oauth/access_token
   - loaded from environment variables
   - constructed dynamically

3. Find whether there are multiple redirect URI values.

4. Specifically check for differences such as:
   https://apps.orvym.com/dashboard/integrations
   https://apps.orvym.com/dashboard/integrations/
   localhost URLs
   backend callback URLs
   old callback URLs
   dynamically generated URLs

5. Determine which redirect URI the CURRENT Meta authorization code is actually issued against.

6. Compare that with the redirect_uri currently being sent to:
   https://graph.facebook.com/v26.0/oauth/access_token

7. Fix the mismatch using the correct OAuth flow for the EXISTING Meta WhatsApp Embedded Signup implementation.

8. Do NOT blindly remove redirect_uri.

9. Do NOT invent a new redirect URI.

10. Do NOT change:
    App ID
    Config ID
    response_type
    override_default_response_type
    sessionInfoVersion
    Meta SDK initialization
    existing message listener
    existing OAuth code extraction
    existing WABA fallback

11. Preserve the current successful behavior:
    FB.login popup opens
    OAuth code is received
    backend callback is called

12. The ONLY immediate goal is to restore:

    OAuth code
       ↓
    backend
       ↓
    Meta token exchange
       ↓
    HTTP 200
       ↓
    access token received
       ↓
    continue to WABA discovery

13. Do NOT stop after receiving the OAuth code.

14. Do NOT consume the OAuth code more than once. It is single-use and expires quickly.

15. Add temporary safe diagnostic logging that shows:

    AUTHORIZATION REDIRECT URI
    TOKEN EXCHANGE REDIRECT URI
    WHETHER THEY MATCH

    Never log client_secret or access_token.

16. Once token exchange returns HTTP 200, keep the existing WABA discovery code untouched and allow the flow to proceed.

IMPORTANT:
We previously reached WABA discovery. Do not regress the application by changing the WABA logic while fixing this OAuth regression.

Make the SMALLEST possible code change.

After the fix, test a completely fresh Embedded Signup attempt and confirm that the backend logs show:

Status Code: 200
Access token received: YES
Token exchange successful

Then confirm that Step 2/WABA discovery starts.

If Step 2 produces Missing Permission again, STOP there and report that separately. Do not mix the Step 1 OAuth fix with the Step 2 permissions fix.