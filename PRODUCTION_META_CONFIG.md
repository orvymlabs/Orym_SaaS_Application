# Meta Dashboard Configuration for Production

## How the Embedded Signup redirect_uri actually works

Meta WhatsApp **Embedded Signup** is launched with the JS SDK:

```js
FB.login(fbLoginCallback, {
  config_id: "2432311603846818",
  response_type: "code",
  override_default_response_type: true,
  extras: { setup: {} },
});
```

The exchangeable code is returned to the page via the JavaScript callback — **not** via a
URL redirect. Therefore **no redirect_uri is used during authorization**, and per Meta's
Embedded Signup documentation ("Onboarding business customers as a Tech Provider") the code
exchange `GET /oauth/access_token` must **also omit `redirect_uri`**.

Sending `redirect_uri` in the token exchange produces:

```
400 Error validating verification code. Please make sure your redirect_uri is identical
    to the one you used in the OAuth dialog request
```

The frontend must send `{ code }` ONLY to the backend callback. The backend must send
`client_id`, `client_secret`, `code` ONLY to Meta.

## Required Changes in Meta App Dashboard

The frontend runs at `https://apps.orvym.com/dashboard/integrations`. Meta validates the
domain of the page that spawned the flow, so **the ACTUAL domain `apps.orvym.com`** must be
registered in all three places below. Do NOT add random domains — only the real one.

### Step 1: App Domains (Settings > Basic)

1. Go to: https://developers.facebook.com/apps/3862862217342382/settings/basic/
2. In **"App Domains"** add (the domain hosting the frontend):
   ```
   apps.orvym.com
   ```
3. Click **"Save Changes"**

### Step 2: Valid OAuth Redirect URIs (Facebook Login > Settings)

1. Go to: https://developers.facebook.com/apps/3862862217342382/fb-login/settings/
2. In **"Valid OAuth Redirect URIs"** add the page URL(s):
   ```
   https://apps.orvym.com/
   https://apps.orvym.com/dashboard/integrations
   ```
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
2. Under **Settings** ensure OAuth is enabled and add the same entries as Step 2/3
   (`https://apps.orvym.com/`, `https://apps.orvym.com/dashboard/integrations`,
   `apps.orvym.com`)

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
- The token exchange is sending a redirect_uri. Remove it — Embedded Signup exchange is
  `client_id + client_secret + code` only (backend `meta_oauth.py` handles this)

**"URL Blocked: This redirect failed because the redirect URI is not whitelisted"**
- Add `https://apps.orvym.com/` and `https://apps.orvym.com/dashboard/integrations`
  to Valid OAuth Redirect URIs (Step 2)
