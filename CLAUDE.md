IMPORTANT — latest production logs prove the previous fix is NOT correct.

The backend is currently sending:

redirect_uri = ''

to:

GET https://graph.facebook.com/v26.0/oauth/access_token

Meta still returns:

Error code: 100
Error subcode: 36008
OAuthException
Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request

Do NOT use an empty redirect_uri.

Do NOT try multiple redirect_uri values.

Do NOT use the backend callback URL simply because the frontend POSTs to that endpoint. The backend callback endpoint and OAuth redirect_uri are two different concepts.

Inspect the actual FB.login({ config_id, response_type: "code", override_default_response_type: true, extras: ... }) implementation and Meta configuration and determine the exact redirect URI Meta binds to the generated authorization code.

Then use that exact same value during /oauth/access_token exchange.

The frontend → backend POST endpoint can remain:

https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback

That is the server callback/API endpoint and does NOT automatically mean it is the OAuth redirect_uri.

Also, opening the backend callback URL directly in a browser produces 405 Method Not Allowed because the endpoint expects POST. Do not treat that as the Meta OAuth redirect URI.

Do not change the working code reception. The 451-character code is being received correctly. Fix only the authorization-code → Meta token exchange mismatch.

After the fix, the logs MUST show the actual non-empty canonical redirect URI being used, and the authorization and token exchange must use the exact same value.

## Repository hygiene

Do NOT create new markdown documentation files in the project root — it gets
cluttered fast. All docs (setup guides, fix summaries, status reports,
checklists, etc.) go under `docs/**`, organized by topic (see
`docs/README.md` for the existing categories: `meta-whatsapp/`,
`production/`, `development/`, `design/`, `features/`). Only `README.md` and
`CLAUDE.md` belong at the root.