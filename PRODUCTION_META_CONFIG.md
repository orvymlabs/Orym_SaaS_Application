# Meta Dashboard Configuration for Production

## How the Embedded Signup redirect_uri actually works (CORRECTED)

WhatsApp **Embedded Signup** is launched with a **manual OAuth dialog URL** that we
build ourselves (Meta's "Manually Build a Login Flow"). Because we build the URL, we
**control `redirect_uri`** and therefore the token exchange can send the **EXACT same
value** Meta recorded in the dialog request:

```
Dialog request:
https://www.facebook.com/v26.0/dialog/oauth
  ?client_id=3862862217342382
  &redirect_uri=https://apps.orvym.com/dashboard/integrations
  &response_type=code
  &config_id=2432311603846818
  &override_default_response_type=true
  &state=<csrf-state>

Token exchange (backend -> Meta):
GET https://graph.facebook.com/v26.0/oauth/access_token
  ?client_id=3862862217342382
  &client_secret=<APP_SECRET>
  &code=<CODE>
  &redirect_uri=https://apps.orvym.com/dashboard/integrations   <-- EXACT same value
```

Meta binds the authorization code to the dialog's `redirect_uri`. Any mismatch
(empty string, another URL, trailing-slash difference) produces:

```
400 Error validating verification code. Please make sure your redirect_uri is identical
    to the one you used in the OAuth dialog request
```

### Rules

- **NEVER send `redirect_uri=""`** (empty string). It is never identical to the value
  Meta recorded and always fails.
- The frontend computes the redirect URI at runtime:
  `window.location.origin + window.location.pathname` (e.g.
  `https://apps.orvym.com/dashboard/integrations`).
- The backend forwards that value **verbatim** in `GET /oauth/access_token`.
- The Redirect URI registered in Meta must match the live page URL **exactly**,
  including the trailing slash.

## Required Changes in Meta App Dashboard

The frontend runs at `https://apps.orvym.com/dashboard/integrations`. Meta validates
the domain of the page that spawned the flow, so **the ACTUAL domain `apps.orvym.com`**
must be registered in all three places below. Do NOT add random domains — only the real one.

### Step 1: App Domains (Settings > Basic)

1. Go to: https://developers.facebook.com/apps/3862862217342382/settings/basic/
2. In **"App Domains"** add (the domain hosting the frontend):
   ```
   apps.orvym.com
   ```
3. Click **"Save Changes"**

### Step 2: Valid OAuth Redirect URIs (Facebook Login > Settings)

The redirect URI in the dialog and the exchange is the integrations page URL. Add the
page URL **with and without** the trailing slash (depending on how your host serves it),
plus the bare origin:

```
https://apps.orvym.com/
https://apps.orvym.com/dashboard/integrations
https://apps.orvym.com/dashboard/integrations/
```

1. Go to: https://developers.facebook.com/apps/3862862217342382/fb-login/settings/
2. In **"Valid OAuth Redirect URIs"** add the entries above.
3. Click **"Save Changes"**

### Step 3: Allowed Domains for the JavaScript SDK (Facebook Login > Settings)

1. In the same Facebook Login > Settings page
2. Find **"Allowed Domains for the JavaScript SDK"**
3. Add:
   ```
   apps.orvym.com
   ```
4. Click **"Save Changes"**

### Step 4: Login for Business settings (Facebook Login for Business)

1. Go to **Facebook Login for Business** in the left sidebar
2. Under **Settings** ensure **Client OAuth Login**, **Web OAuth Login**, **Enforce
   HTTPS**, **Login with JavaScript SDK** are enabled and add the same entries as
   Step 2/3 (`https://apps.orvym.com/`,
   `https://apps.orvym.com/dashboard/integrations`,
   `https://apps.orvym.com/dashboard/integrations/`, `apps.orvym.com`)

### Step 5: Verify Webhook Configuration (WhatsApp > Configuration)

1. **Webhook URL**:
   ```
   https://orym-saas-application.onrender.com/webhook
   ```
2. **Verify Token** must match what's in the database

## Troubleshooting

**"Can't load URL: The domain of this URL isn't included in the app's domains."**
- `apps.orvym.com` is missing from App Domains and/or "Allowed Domains for the JavaScript SDK"
- Add it (Steps 1 and 3 above)

**"Error validating verification code... redirect_uri"**
- The token exchange sent a `redirect_uri` that differs from the one in the dialog
  (trailing slash, scheme, or empty string). The value in
  `GET /oauth/access_token` must be byte-for-byte identical to the dialog's
  `redirect_uri` and must be registered in Valid OAuth Redirect URIs.

**"URL Blocked: This redirect failed because the redirect URI is not whitelisted"**
- Add `https://apps.orvym.com/`, `https://apps.orvym.com/dashboard/integrations`
  and the trailing-slash variant to Valid OAuth Redirect URIs (Step 2)
