vI need you to replace ONLY the existing WhatsApp Embedded Signup implementation in the ORVYM SaaS application.

Use the official Meta WhatsApp Embedded Signup implementation below as the PRIMARY SOURCE OF TRUTH.

Do not patch the current custom implementation.

Remove the old Embedded Signup-specific implementation and rebuild it using the official Meta flow below, adapted properly for our existing Next.js/React application.

==================================================
STRICT SCOPE — DO NOT TOUCH ANYTHING ELSE
=========================================

ONLY modify the WhatsApp Embedded Signup implementation.

DO NOT modify:

* Login
* Signup
* Registration
* Authentication
* Authorization
* Sessions
* User accounts
* Existing dashboard
* Existing database
* Existing APIs unrelated to Embedded Signup
* Existing WhatsApp functionality unrelated to Embedded Signup
* Existing application logic
* Existing UI unrelated to Embedded Signup
* Any other integration
* Any other working functionality

DO NOT refactor unrelated files.

DO NOT upgrade unrelated dependencies.

DO NOT rebuild authentication.

DO NOT create a new login system.

DO NOT create a new signup system.

The existing ORVYM authentication must remain exactly as it currently works.

The user is already logged into ORVYM.

Embedded Signup is ONLY used when the existing logged-in user clicks the existing WhatsApp connection button.

==================================================
OFFICIAL META EMBEDDED SIGNUP IMPLEMENTATION
============================================

Use the following official Meta implementation as the basis of the new implementation.

### SDK LOADING

```html
<!-- SDK loading -->
<script async defer crossorigin="anonymous"
  src="https://connect.facebook.net/en_US/sdk.js"></script>
```

Load the Facebook JavaScript SDK correctly in the existing Next.js/React application.

Do not literally paste raw HTML into a React component if that is not appropriate.

Adapt it correctly to the existing framework.

==================================================
SDK INITIALIZATION
==================

Use the official Meta initialization pattern:

```javascript
// SDK initialization
window.fbAsyncInit = function() {
  FB.init({
    appId: '<APP_ID>',
    autoLogAppEvents: true,
    xfbml: true,
    version: '<GRAPH_API_VERSION>'
  });
};
```

Use:

App ID:

3862862217342382

For Graph API version, use the latest version required by the current official Meta documentation.

Do not invent another App ID.

Do not create another Meta App.

Do not create another Config ID unless absolutely required.

==================================================
SESSION LOGGING MESSAGE EVENT
=============================

Implement the official Meta message event listener:

```javascript
// Session logging message event listener
window.addEventListener('message', (event) => {
  if (!event.origin.endsWith('facebook.com')) return;

  try {
    const data = JSON.parse(event.data);

    if (data.type === 'WA_EMBEDDED_SIGNUP') {
      console.log('message event: ', data);
      // your code goes here
    }
  } catch {
    console.log('message event: ', event.data);
    // your code goes here
  }
});
```

Adapt this properly for production React/Next.js.

The event listener must be registered only once.

Clean it up correctly when the component unmounts.

Do not create duplicate listeners.

Do not process the same event multiple times.

==================================================
IMPORTANT — WA_EMBEDDED_SIGNUP
==============================

Do NOT use the old custom:

SDK_QUERY_STRING

implementation.

The current implementation incorrectly relies on SDK_QUERY_STRING and therefore reports:

waba_id: MISSING
phone_number_id: MISSING
business_id: MISSING

Replace that logic completely.

Use:

data.type === 'WA_EMBEDDED_SIGNUP'

as specified by the official Meta implementation.

The successful flow can return:

```javascript
{
  data: {
    phone_number_id: '<CUSTOMER_BUSINESS_PHONE_NUMBER_ID>',
    waba_id: '<CUSTOMER_WABA_ID>',
    business_id: '<CUSTOMER_BUSINESS_PORTFOLIO_ID>',

    // only included if customer selected ad accounts
    ad_account_ids: [
      '<CUSTOMER_AD_ACCOUNT_ID_1>',
      '<CUSTOMER_AD_ACCOUNT_ID_2>'
    ],

    // only included if customer selected Facebook Pages
    page_ids: [
      '<CUSTOMER_PAGE_ID_1>',
      '<CUSTOMER_PAGE_ID_2>'
    ],

    // only included if customer selected datasets
    dataset_ids: [
      '<CUSTOMER_DATASET_ID_1>',
      '<CUSTOMER_DATASET_ID_2>'
    ],

    // only included if customer selected catalogs
    catalog_ids: [
      '<CUSTOMER_CATALOG_ID_1>',
      '<CUSTOMER_CATALOG_ID_2>'
    ],

    // only included if customer selected Instagram accounts
    instagram_account_ids: [
      '<CUSTOMER_IG_ACCOUNT_ID_1>',
      '<CUSTOMER_IG_ACCOUNT_ID_2>'
    ],

    // only included for multi-WABA flows
    waba_ids: [
      '<CUSTOMER_WABA_ID_1>',
      '<CUSTOMER_WABA_ID_2>'
    ]
  },

  type: 'WA_EMBEDDED_SIGNUP',

  event: '<FLOW_FINISH_TYPE>'
}
```

Correctly extract and process:

* phone_number_id
* waba_id
* business_id

when they are provided.

Do not fabricate missing values.

Do not hardcode these IDs.

==================================================
FLOW FINISH TYPES
=================

Handle the official Meta flow completion values:

```text
FINISH
FINISH_ONLY_WABA
FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING
FINISH_OBO_MIGRATION
FINISH_GRANT_ONLY_API_ACCESS
ERROR
```

`FINISH` indicates successful Cloud API flow completion.

`FINISH_ONLY_WABA` indicates completion without adding a phone number.

`FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING` indicates completion with a WhatsApp Business App number.

`FINISH_OBO_MIGRATION` indicates an on-behalf-of migration flow.

`FINISH_GRANT_ONLY_API_ACCESS` indicates grant-only API access.

`ERROR` indicates the customer encountered an error.

Handle these according to the actual data returned.

==================================================
ABANDONED FLOW
==============

Handle the official Meta cancellation structure:

```javascript
{
  data: {
    current_step: '<CURRENT_STEP>',
  },
  type: 'WA_EMBEDDED_SIGNUP',
  event: 'CANCEL',
}
```

Capture `current_step`.

Do not treat a normal successful finish/close as cancellation when Meta reports it as a successful completion.

According to Meta's documentation, on the final screen, clicking Finish or closing the popup can still represent successful onboarding.

==================================================
USER REPORTED ERRORS
====================

Handle the official error structure:

```javascript
{
  data: {
    error_message: '<ERROR_MESSAGE>',
    error_code: '<ERROR_CODE>',
    session_id: '<SESSION_ID>',
    timestamp: '<TIMESTAMP>',
  },
  type: 'WA_EMBEDDED_SIGNUP',
  event: 'CANCEL',
}
```

Capture:

* error_message
* error_code
* session_id
* timestamp

Use this information for debugging/error handling.

Do not expose sensitive internal information to the user.

==================================================
RESPONSE CALLBACK
=================

Implement the official Meta response callback:

```javascript
// Response callback
const fbLoginCallback = (response) => {
  if (response.authResponse) {
    const code = response.authResponse.code;
    console.log('response: ', code);
    // your code goes here
  } else {
    console.log('response: ', response);
    // your code goes here
  }
}
```

Adapt it properly to React/Next.js.

When:

```javascript
response.authResponse
```

exists, retrieve:

```javascript
response.authResponse.code
```

This is the exchangeable token code.

Immediately send this code to the backend.

Do not wait for another user action.

Do not manually exchange it from the frontend.

Do not expose App Secret.

Do not expose customer access tokens.

The exchangeable code has a TTL of approximately 30 seconds, so process it immediately.

Do not log the complete code in production.

==================================================
LAUNCH METHOD
=============

Implement the official Meta launch method:

```javascript
// Launch method and callback registration
const launchWhatsAppSignup = () => {
  FB.login(fbLoginCallback, {
    config_id: '<CONFIGURATION_ID>',
    response_type: 'code',
    override_default_response_type: true,
    extras: {
      setup: {},
    }
  });
}
```

Use:

Configuration ID:

2432311603846818

Use:

```text
response_type: 'code'
override_default_response_type: true
extras: {
  setup: {}
}
```

Do not replace this with the old custom OAuth implementation.

==================================================
LAUNCH BUTTON
=============

Do NOT replace the existing ORVYM UI unnecessarily.

The existing Connect WhatsApp button should remain.

Only replace the underlying Embedded Signup launch logic.

The official example button:

```html
<!-- Launch button -->
<button
  onclick="launchWhatsAppSignup()"
  style="background-color: #1877f2; border: 0; border-radius: 4px; color: #fff; cursor: pointer; font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: bold; height: 40px; padding: 0 24px;">
  Login with Facebook
</button>
```

is only an example.

Do NOT change the ORVYM dashboard UI to a "Login with Facebook" button.

Keep the existing ORVYM WhatsApp connection button and connect it to the new `launchWhatsAppSignup` logic.

==================================================
BACKEND PROCESSING
==================

The official Meta documentation states that the exchangeable code should be sent to the server and then exchanged for the customer's business token during onboarding.

Implement this server-side.

The backend must securely process the exchangeable code using the current Meta-documented flow.

Do not expose:

* App Secret
* access tokens
* client secrets

to the browser.

Use the existing authenticated ORVYM user.

DO NOT modify authentication.

DO NOT modify login.

DO NOT modify signup.

Do not create a new authentication mechanism.

After Meta processing succeeds, pass the resulting WhatsApp account information into the EXISTING ORVYM WhatsApp connection mechanism.

Do not rebuild the entire WhatsApp system.

==================================================
REDIRECT URI — IMPORTANT
========================

The OLD implementation currently fails with:

HTTP 400

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

Do NOT blindly preserve this old custom redirect_uri logic.

Follow the official Meta Embedded Signup implementation above.

Determine from the CURRENT Meta documentation and implementation whether this specific flow requires the old redirect_uri handling.

If the old redirect_uri validation is obsolete for this implementation, remove ONLY that obsolete Embedded Signup logic.

If Meta requires a redirect URI for the actual flow being used, implement exactly what Meta currently requires.

Do not modify application login redirects.

Do not modify signup redirects.

Do not modify authentication callbacks.

Do not introduce localhost.

Production frontend:

https://apps.orvym.com

Production backend:

https://orym-saas-application.onrender.com

==================================================
DUPLICATE EXECUTION
===================

The old implementation sometimes launches Embedded Signup twice.

Fix this only inside Embedded Signup.

Required behavior:

ONE CLICK
→ ONE FB.login()
→ ONE Embedded Signup session
→ ONE exchangeable code
→ ONE backend request

Prevent duplicate event listeners.

Prevent duplicate code processing.

Prevent duplicate backend requests.

Still allow retry after cancellation or failure.

==================================================
NEXT.JS / REACT ADAPTATION
==========================

The official Meta example is plain HTML/JavaScript.

Our application is already built with Next.js/React.

Convert the official implementation correctly into the existing React architecture.

Do not literally inject the entire HTML example into the page.

Use the appropriate React lifecycle for:

* SDK loading
* SDK initialization
* message listener registration
* message listener cleanup
* FB.login invocation
* callback handling

Do not create unnecessary architecture.

Do not change unrelated components.

==================================================
CURRENT PROBLEM TO FIX
======================

Current logs show:

Facebook SDK initialized

Embedded Signup launches

SDK_QUERY_STRING received

exchangeable code received

but:

waba_id: MISSING
phone_number_id: MISSING
business_id: MISSING

and then:

POST /api/integrations/meta/oauth/callback

returns:

400 Bad Request

"Error validating verification code. Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request"

The new implementation must remove the incorrect old SDK_QUERY_STRING dependency and implement the official `WA_EMBEDDED_SIGNUP` event handling plus official `FB.login` response callback.

==================================================
IMPORTANT IMPLEMENTATION RULE
=============================

Do not simply add the official code alongside the old code.

REMOVE the old Embedded Signup implementation.

There must be ONE active Embedded Signup implementation after the change.

Do not leave duplicate:

* FB.login handlers
* message listeners
* code processors
* callbacks
* Embedded Signup components

==================================================
SUCCESS FLOW
============

The final flow should be:

Existing ORVYM logged-in user
↓
Existing Connect WhatsApp button
↓
Official Meta Embedded Signup
↓
User completes onboarding
↓
WA_EMBEDDED_SIGNUP message received
↓
phone_number_id / waba_id / business_id captured when provided
↓
FB.login callback receives exchangeable code
↓
Code immediately sent to backend
↓
Backend securely performs required Meta processing
↓
Existing ORVYM WhatsApp connection completes
↓
Dashboard shows WhatsApp connected

==================================================
TESTING
=======

Test the complete production flow.

Verify:

[ ] Facebook SDK initializes once
[ ] Existing Connect WhatsApp button still works
[ ] Embedded Signup opens once
[ ] Official Config ID is used
[ ] WA_EMBEDDED_SIGNUP event is received
[ ] phone_number_id is captured when provided
[ ] waba_id is captured when provided
[ ] business_id is captured when provided
[ ] FB.login callback receives the exchangeable code
[ ] Code is sent to backend immediately
[ ] Backend processes the code successfully
[ ] Existing WhatsApp connection completes
[ ] No redirect_uri mismatch remains
[ ] Cancellation works
[ ] Error handling works
[ ] Retry works
[ ] Existing login still works
[ ] Existing signup still works
[ ] Existing authentication still works

==================================================
FINAL STRICT RULE
=================

This is ONLY a WhatsApp Embedded Signup replacement.

DO NOT TOUCH:

AUTH
LOGIN
SIGNUP
REGISTRATION
SESSIONS
USER MANAGEMENT
DATABASE ARCHITECTURE
UNRELATED APIs
UNRELATED UI
UNRELATED FEATURES
UNRELATED INTEGRATIONS

Use the official Meta Embedded Signup code and documentation provided above.

Make the smallest possible isolated change.

The task is complete only when the Embedded Signup flow works end-to-end in production.
