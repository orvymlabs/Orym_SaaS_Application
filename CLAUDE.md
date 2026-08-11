IMPORTANT: DO NOT REWRITE OR REDESIGN THE EXISTING WHATSAPP EMBEDDED SIGNUP FLOW.

The flow was previously working up to the Meta OAuth token exchange. A recent change broke that working behavior by removing redirect_uri from the token exchange.

CURRENT PROBLEM:

Backend log now shows:

Parameter names: ['client_id', 'client_secret', 'code']
redirect_uri included: False
redirect_uri value: OMITTED

Meta returns:

Error Code: 100
Error Subcode: 36008
Error Type: OAuthException
Error Message:
"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

THIS CHANGE MUST BE REVERTED.

GOAL:

Restore the previously working OAuth token exchange EXACTLY as it was, then fix only the remaining flow after that point.

==================================================
1. RESTORE REDIRECT_URI IN TOKEN EXCHANGE
==================================================

The backend MUST send redirect_uri to:

https://graph.facebook.com/v26.0/oauth/access_token

The request MUST contain:

client_id
client_secret
code
redirect_uri

Use this exact redirect URI:

https://apps.orvym.com/dashboard/integrations/

The trailing slash MUST remain.

Do NOT omit redirect_uri.

Do NOT use:
https://apps.orvym.com/dashboard/integrations

Do NOT use another callback URL.

Do NOT create a second redirect URI.

The same exact URI must be used consistently by the existing frontend OAuth flow and backend token exchange.

==================================================
2. DO NOT BREAK THE EXISTING FRONTEND FLOW
==================================================

The following is ALREADY working and MUST NOT be rewritten:

- Facebook SDK initialization
- App ID: 3862862217342382
- FB.login popup
- Config ID: 2432311603846818
- response_type=code
- override_default_response_type=true
- extras:
  {
    "setup": {},
    "sessionInfoVersion": 3
  }
- window message listener
- OAuth code extraction
- non-JSON OAuth redirect fallback
- LOGIN_CODE_RECEIVED handling

The frontend is successfully receiving a 451-character OAuth code.

For example:

[EmbeddedSignup] OAuth code detected in non-JSON redirect message
[EmbeddedSignup] code received
[EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451)

Therefore DO NOT change the OAuth code extraction logic.

==================================================
3. DO NOT FIX THE WRONG THING
==================================================

Do NOT remove the fallback OAuth-code handling.

Do NOT require WA_EMBEDDED_SIGNUP event before accepting the OAuth code.

Do NOT change FB.login to another OAuth implementation.

Do NOT replace the official Meta Embedded Signup flow.

Do NOT change the Config ID.

Do NOT change the App ID.

Do NOT change permissions just because the previous WABA discovery error existed.

First restore the working token exchange.

==================================================
4. VERIFY THE TOKEN EXCHANGE
==================================================

After the fix, logs MUST show:

META OAUTH TOKEN EXCHANGE

Parameter names:
['client_id', 'client_secret', 'code', 'redirect_uri']

redirect_uri included: True

redirect_uri value:
https://apps.orvym.com/dashboard/integrations/

Then Meta should return:

Status Code: 200
Access token received: YES
Token exchange successful

The expected sequence is:

Step 1/6 - Meta token exchange started
→ Meta token exchange successful

Only after this succeeds should the code continue to the next Embedded Signup step.

==================================================
5. CONTINUE THE EXISTING FLOW AFTER TOKEN EXCHANGE
==================================================

Once token exchange succeeds, DO NOT stop.

Continue the existing flow:

OAuth code
→ access token
→ WABA/business discovery
→ Embedded Signup session information
→ WABA ID
→ phone_number_id
→ business_id
→ integration creation
→ save integration
→ return success to frontend

Use the existing implementation wherever possible.

Do not rewrite these parts unless there is an actual error after Step 1.

==================================================
6. IMPORTANT ABOUT WA_EMBEDDED_SIGNUP FINISH
==================================================

The frontend currently receives the OAuth code even when the WA_EMBEDDED_SIGNUP message is not received.

Example:

LOGIN_CODE_RECEIVED (length: 451)

Therefore the frontend MUST NOT block the backend OAuth flow solely because:

WA_EMBEDDED_SIGNUP FINISH event never arrived

The OAuth code should continue through the existing fallback path.

If WABA/phone IDs are available from the Embedded Signup session event, use them.

If they are not available, preserve the existing server-side discovery mechanism.

Do NOT make the entire OAuth flow fail just because the optional session message is delayed/missing.

==================================================
7. SEARCH BEFORE MODIFYING
==================================================

Search the entire codebase for:

oauth/access_token
redirect_uri
META_REDIRECT_URI
FACEBOOK_REDIRECT_URI
META_OAUTH_REDIRECT_URI
FB.login
config_id
WA_EMBEDDED_SIGNUP
LOGIN_CODE_RECEIVED

Find the code that previously included redirect_uri in the token exchange.

Restore that behavior instead of creating a completely new implementation.

==================================================
8. DO NOT BREAK OTHER FEATURES
==================================================

This is a production SaaS application.

DO NOT modify unrelated:

- authentication
- bots
- notifications
- dashboard
- database models
- existing integrations
- frontend layout
- API routes unrelated to Meta
- CSS
- popup behavior

Only modify the minimum code required for Meta Embedded Signup.

==================================================
9. DO NOT MAKE RANDOM "FIXES"
==================================================

Do NOT:

- remove redirect_uri
- change the App ID
- change the Config ID
- change the Meta API version unless absolutely required
- replace FB.login
- replace the message listener
- remove the OAuth fallback
- disable security checks
- hardcode access tokens
- log client secrets
- log OAuth codes
- rewrite the complete integration

The OAuth code and client secret MUST NEVER be printed in logs.

==================================================
10. FINAL VERIFICATION
==================================================

After making the change, test the complete flow from a fresh WhatsApp Embedded Signup attempt.

Expected:

Frontend:

Message listener registered
Facebook SDK initialized
Launching WhatsApp Embedded Signup
OAuth code received

Backend:

Step 1/6 - Meta token exchange started
redirect_uri included: True
redirect_uri value: https://apps.orvym.com/dashboard/integrations/
Token exchange successful

Then:

Step 2/6 and subsequent steps continue normally.

If another error occurs AFTER Step 1 succeeds, DO NOT undo the redirect_uri fix.

Instead diagnose the NEW error as the next stage of the flow.

FINAL REQUIREMENT:

The priority is:

1. RESTORE the previously working redirect_uri behavior.
2. Confirm Meta token exchange returns HTTP 200.
3. Continue the existing flow after token exchange.
4. Fix only the next actual error encountered.
5. Do NOT break any previously working part.