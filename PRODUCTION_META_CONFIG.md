# Meta Dashboard Configuration for Production

## How Embedded Signup actually works (CORRECTED - current official flow)

WhatsApp **Embedded Signup** is launched with the **Facebook JavaScript SDK** using
`FB.login()` with the app's `config_id` (Meta's official "Embedded Signup
Implementation" flow - Facebook Login for Business). We do NOT build a manual OAuth
dialog URL. The flow:

```
FB.login(callback, {
  config_id: '<CONFIG_ID>',               // Embedded Signup configuration ID
  response_type: 'code',
  override_default_response_type: true,
  extras: { setup: {}, sessionInfoVersion: 3 }
})
```

- The exchangeable code is returned to the JS popup callback
  (`response.authResponse.code`) - there is NO server-side redirect.
- The customer's asset IDs (`waba_id`, `phone_number_id`, `business_id`) are returned
  via the `WA_EMBEDDED_SIGNUP` message event posted to the window that spawned the
  flow.

### Token exchange (backend -> Meta)

```
GET https://graph.facebook.com/v26.0/oauth/access_token
  ?client_id=<APP_ID>
  &client_secret=<APP_SECRET>
  &code=<CODE>
```

**NO `redirect_uri` is sent.** Per Meta's current official Embedded Signup docs the
exchangeable code is returned directly to the JS popup callback, so no server-side
redirect URI exists. Sending ANY `redirect_uri` (including the JS SDK's internal
`https://staticxx.facebook.com/x/connect/xd_arbiter/?version=46` channel URL, an empty
string, or `facebook.com/connect/login_success.html`) triggers Meta error code 191
("The domain of this URL isn't included in the app's domains") or "Error validating
verification code".

### Session data gating (why the WA_EMBEDDED_SIGNUP message must arrive)

From Meta's official Implementation doc (verbatim requirement):

> Embedded Signup returns the customer's WhatsApp Business account (WABA) ID, business
> phone number ID, and an exchangeable token code to the window that spawned the flow,
> but only if the domain of the page that spawned the flow is listed in the **Allowed
> domains** and **Valid OAuth redirect URIs** fields.

The code is delivered through the JavaScript SDK callback channel. The
`WA_EMBEDDED_SIGNUP` session message is a separate `window.postMessage` to the spawning
page and is delivered ONLY when the spawning domain is present in BOTH fields. If the
code arrives but the session event never fires, the spawning domain is missing from one
of those two fields in the Meta App Dashboard.

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

### Step 2: Facebook Login for Business > Settings > Client OAuth settings

1. Go to: https://developers.facebook.com/apps/3862862217342382/fb-login/settings/
   (or the "Facebook Login for Business" product settings)
2. Set the following to **Yes**:
   - Client OAuth Login
   - Web OAuth Login
   - Enforce HTTPS
   - Embedded Browser OAuth Login
   - Use Strict Mode for redirect URIs
   - Login with the JavaScript SDK
3. In **"Valid OAuth Redirect URIs"** add the page URL and the bare origin
   (required for the WA_EMBEDDED_SIGNUP session message to be delivered):
   ```
   https://apps.orvym.com/
   https://apps.orvym.com/dashboard/integrations
   https://apps.orvym.com/dashboard/integrations/
   ```
4. In **"Allowed Domains for the JavaScript SDK"** add:
   ```
   apps.orvym.com
   ```
5. Click **"Save Changes"**

Do NOT add `staticxx.facebook.com` to App Domains or to any allowlist — it is a
Meta-internal SDK domain and is never a legitimate redirect target.

### Step 3: Verify the Embedded Signup Configuration

1. In the Meta App Dashboard open **Facebook Login for Business > Configurations**.
2. Confirm the configuration with ID **2432311603846818** exists, belongs to App ID
   **3862862217342382**, and uses the **WhatsApp Embedded Signup** login variation.
3. Confirm the config's session info version is **3** (the frontend sends
   `sessionInfoVersion: 3`; under Embedded Signup v2 a sessionInfoVersion is required
   to receive the callback). v2/v3 configs are deprecated on October 15, 2026 - plan
   a v4 config (created via Configurations, which auto-selects v4).

### Step 4: Verify Webhook Configuration (WhatsApp > Configuration)

1. **Webhook URL**:
   ```
   https://orym-saas-application.onrender.com/webhook
   ```
2. **Verify Token** must match what's in the database

## Troubleshooting

**"Can't load URL: The domain of this URL isn't included in the app's domains."**
- `apps.orvym.com` is missing from App Domains and/or "Allowed Domains for the JavaScript SDK"
- Add it (Step 1 and Step 2.4 above)

**Code received but the WA_EMBEDDED_SIGNUP session message (waba_id / phone_number_id) never arrives**
- The spawning domain is missing from "Valid OAuth redirect URIs" and/or "Allowed
  domains" in Facebook Login for Business > Settings (Step 2.3/2.4). This is the
  documented gating condition for the session message. The backend recovers
  WABA/phone IDs server-side via `/debug_token` granular scopes + the WABA
  `phone_numbers` edge when the session message is absent.

**"Error validating verification code... redirect_uri"**
- The token exchange must send ONLY `client_id + client_secret + code` (no
  `redirect_uri`). Remove any `redirect_uri` from the exchange request.

**"URL Blocked: This redirect failed because the redirect URI is not whitelisted"**
- Add `https://apps.orvym.com/`, `https://apps.orvym.com/dashboard/integrations`
  and the trailing-slash variant to Valid OAuth Redirect URIs (Step 2.3)
