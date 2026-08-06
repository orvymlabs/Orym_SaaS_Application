The latest production logs show that the previous redirect_uri fix is NOT actually working.

Current logs:

FB.login options:
{
  "config_id": "2432311603846818",
  "response_type": "code",
  "override_default_response_type": true,
  "extras": {
    "setup": {}
  }
}

The frontend explicitly logs:
"redirect_uri is NOT passed in FB.login() options"

Then:
"redirect_uri: NOT INCLUDED"

Then Render returns:
400
"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

There is also:
"Can't load URL: The domain of this URL isn't included in the app's domains."

IMPORTANT:
Do not make assumptions about redirect_uri anymore.

Please inspect the actual Meta Embedded Signup implementation and determine the correct redirect_uri behavior for FB.login() with:
config_id = 2432311603846818
response_type = code
override_default_response_type = true

Then:

1. Inspect the exact frontend code currently deployed to production.
2. Verify whether redirect_uri is actually being passed to FB.login().
3. Inspect the exact request body sent from frontend to:
   /api/integrations/meta/oauth/callback
4. Inspect the backend callback implementation.
5. Inspect the exact parameters sent by backend to Meta's OAuth/token endpoint.
6. Make sure the redirect_uri behavior is consistent between authorization and code exchange.
7. Fix the "domain isn't included in app's domains" issue based on the ACTUAL redirect URI being used.
8. Do not simply add random domains to Meta.
9. Verify the fix against Meta's current Embedded Signup documentation.
10. Build the frontend and verify the production bundle actually contains the fix.

Also note:
Frontend production = https://apps.orvym.com
Backend production = https://orym-saas-application.onrender.com

Do NOT refer to Netlify. Frontend is hosted on Hostinger.

After making changes, tell me:
- exact redirect_uri used
- exact Meta callback/token endpoint
- exact frontend request body
- exact backend request to Meta
- which Meta App Domains / OAuth Redirect URI entries are required