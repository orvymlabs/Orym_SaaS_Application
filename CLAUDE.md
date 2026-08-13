STOP.

The latest production logs prove that the previous redirect_uri change is incorrect.

The backend is now sending:

redirect_uri included: True
redirect_uri value: ''

Meta returns:

Error Code: 100
Error Subcode: 36008
OAuthException

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

Do NOT use an empty redirect_uri.

Do NOT omit it as a guess.

Do NOT try multiple redirect_uri fallbacks.

Do NOT randomly switch between:
- https://apps.orvym.com
- https://apps.orvym.com/dashboard/integrations
- https://apps.orvym.com/dashboard/integrations/
- https://www.facebook.com/connect/login_success.html

The current implementation must be traced properly.

Current frontend launch:

FB.login({
  config_id: "2432311603846818",
  response_type: "code",
  override_default_response_type: true,
  extras: {
    setup: {},
    sessionInfoVersion: 3
  }
})

App ID:
3862862217342382

Config ID:
2432311603846818

Production frontend:
https://apps.orvym.com

Integrations page:
https://apps.orvym.com/dashboard/integrations

Current backend token exchange:

GET
https://graph.facebook.com/v26.0/oauth/access_token

Parameters currently:
client_id
client_secret
code
redirect_uri=""

This is wrong.

FIRST determine exactly how Meta binds the authorization code to the OAuth redirect context for THIS Embedded Signup Config ID + FB.login implementation.

Inspect:
1. Current FB.login implementation.
2. Config ID configuration.
3. Meta App OAuth / Facebook Login for Business configuration.
4. Valid OAuth Redirect URIs.
5. Any frontend environment variables.
6. Any redirect URI passed or generated during authorization.
7. Backend token exchange implementation.
8. Any redirect URI normalization/defaulting logic.

The authorization request and token exchange must use the exact same redirect URI/context expected by Meta.

Do not make multiple attempts.

Do not use an empty string.

Do not hide the Meta error.

Before changing code, identify:
- exact authorization redirect URI/context
- exact Meta configuration
- exact value that must be used in token exchange

Then make the smallest production fix.

Preserve:
- App ID 3862862217342382
- Config ID 2432311603846818
- working Embedded Signup
- working 451-character code reception
- existing ORVYM integration flow

Do not modify unrelated functionality.

After the token exchange succeeds, continue through the existing flow:
CODE
→ BUSINESS TOKEN
→ WABA
→ PHONE NUMBER
→ BUSINESS
→ existing ORVYM connection

Also verify that the code is exchanged exactly once.

Use a completely fresh Embedded Signup code for testing because the code is short-lived and single-use.

Report:
1. Exact root cause
2. Exact redirect URI/context Meta expects
3. Why redirect_uri became ""
4. Files changed
5. Meta configuration involved
6. Final authorization → exchange flow
7. Fresh production test result
8. Any remaining blocker