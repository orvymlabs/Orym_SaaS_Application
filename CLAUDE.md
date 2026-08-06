Step 3: Add Embedded Signup to your website
Add the following HTML and JavaScript code to your website. This is the complete code needed to implement Embedded Signup. Each portion of the code will be explained in detail below.
<!-- SDK loading -->
<script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js"></script>

<script>
  // SDK initialization
  window.fbAsyncInit = function() {
    FB.init({
      appId: '<APP_ID>', // your app ID goes here
      autoLogAppEvents: true,
      xfbml: true,
      version: '<GRAPH_API_VERSION>' // Graph API version goes here
    });
  };

  // Session logging message event listener
  window.addEventListener('message', (event) => {
    if (!event.origin.endsWith('facebook.com')) return;
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'WA_EMBEDDED_SIGNUP') {
        console.log('message event: ', data); // remove after testing
        // your code goes here
      }
    } catch {
      console.log('message event: ', event.data); // remove after testing
      // your code goes here
    }
  });

  // Response callback
  const fbLoginCallback = (response) => {
    if (response.authResponse) {
      const code = response.authResponse.code;
      console.log('response: ', code); // remove after testing
      // your code goes here
    } else {
      console.log('response: ', response); // remove after testing
      // your code goes here
    }
  }

  // Launch method and callback registration
  const launchWhatsAppSignup = () => {
    FB.login(fbLoginCallback, {
      config_id: '<CONFIGURATION_ID>', // your configuration ID goes here
      response_type: 'code',
      override_default_response_type: true,
      extras: {
        setup: {},
      }
    });
  }
</script>

<!-- Launch button  -->
<button onclick="launchWhatsAppSignup()" style="background-color: #1877f2; border: 0; border-radius: 4px; color: #fff; cursor: pointer; font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: bold; height: 40px; padding: 0 24px;">Login with Facebook</button>
SDK loading
The following script tag loads the Facebook JavaScript SDK asynchronously:
<!-- SDK loading -->
<script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js"></script>
SDK initialization
This portion of the code initializes the SDK. Add your app ID and the latest Graph API version here.
// SDK initialization
window.fbAsyncInit = function() {
  FB.init({
    appId: '<APP_ID>', // your app ID goes here
    autoLogAppEvents: true,
    xfbml: true,
    version: '<GRAPH_API_VERSION>' // Graph API version here
  });
};
Replace the following placeholders with your own values.
Placeholder	Description	Example value
<APP_ID>
Required.
Your app ID. This is displayed at the top of the App Dashboard.
21202248997039
<GRAPH_API_VERSION>
Required.
Graph API version. This indicates which version of Graph API to call, if you are relying on the SDK’s methods to perform API calls.
In the context of Embedded Signup, you won’t be relying on the SDK’s methods to perform API calls. Set this to the latest API version:
v26.0
v26.0
Session logging message event listener
The message event listener captures the following critical information:
The business customer’s newly generated asset IDs, if they successfully completed the flow
The name of the screen they abandoned, if they abandoned the flow
An error ID, if they encountered an error and used the flow to report it
// Session logging message event listener
window.addEventListener('message', (event) => {
  if (!event.origin.endsWith('facebook.com')) return;
  try {
    const data = JSON.parse(event.data);
    if (data.type === 'WA_EMBEDDED_SIGNUP') {
      console.log('message event: ', data); // remove after testing
      // your code goes here
    }
  } catch {
    console.log('message event: ', event.data); // remove after testing
    // your code goes here
  }
});
Embedded Signup sends this information in a message event object to the window that spawned the flow and assigns it to the data constant. Add your own custom code to the try-catch statement that can send this object to your server. The object structure will vary based on flow completion, abandonment, or error reporting, as described below.
Successful flow completion structure:
On the final screen, both clicking Finish and closing the popup (for example, by clicking the X button) are considered successful onboarding. In both scenarios, Embedded Signup returns the exchangeable token code and the session info object containing the customer’s asset IDs. Exiting on the final screen is not considered a cancel event.
{
  data: {
    phone_number_id: '<CUSTOMER_BUSINESS_PHONE_NUMBER_ID>',
    waba_id: '<CUSTOMER_WABA_ID>',
    business_id: '<CUSTOMER_BUSINESS_PORTFOLIO_ID>',

    <!-- only included if customer selected ad accounts -->
    ad_account_ids: ['<CUSTOMER_AD_ACCOUNT_ID_1>', '<CUSTOMER_AD_ACCOUNT_ID_2>'],

    <!-- only included if customer selected Facebook Pages -->
    page_ids: ['<CUSTOMER_PAGE_ID_1>', '<CUSTOMER_PAGE_ID_2>'],

    <!-- only included if customer selected datasets -->
    dataset_ids: ['<CUSTOMER_DATASET_ID_1>', '<CUSTOMER_DATASET_ID_2>'],

    <!-- only included if customer selected catalogs -->
    catalog_ids: ['<CUSTOMER_CATALOG_ID_1>', '<CUSTOMER_CATALOG_ID_2>'],

    <!-- only included if customer selected Instagram accounts -->
    instagram_account_ids: ['<CUSTOMER_IG_ACCOUNT_ID_1>', '<CUSTOMER_IG_ACCOUNT_ID_2>'],

    <!-- only included for multi-WABA flows -->
    waba_ids: ['<CUSTOMER_WABA_ID_1>', '<CUSTOMER_WABA_ID_2>']
  },
  type: 'WA_EMBEDDED_SIGNUP',
  event: '<FLOW_FINISH_TYPE>',
}
Placeholder	Description	Example value
<CUSTOMER_BUSINESS_PHONE_NUMBER_ID>
The business customer’s business phone number ID
106540352242922
<CUSTOMER_WABA_ID>
The business customer’s WhatsApp Business account ID.
524126980791429
<CUSTOMER_BUSINESS_PORTFOLIO_ID>
The business customer’s business portfolio ID.
2729063490586005
<CUSTOMER_AD_ACCOUNT_ID>
Only included if the customer selected ad accounts during the flow. The business customer’s ad account ID.
4052175343162067
<CUSTOMER_PAGE_ID>
Only included if the customer selected Facebook Pages during the flow. The business customer’s Facebook Page ID.
1791141545170328
<CUSTOMER_DATASET_ID>
Only included if the customer selected datasets during the flow. The business customer’s dataset ID.
524126980791429
<CUSTOMER_CATALOG_ID>
Only included if the customer selected catalogs during the flow. The business customer’s catalog ID.
8827498273649182
<CUSTOMER_IG_ACCOUNT_ID>
Only included if the customer selected Instagram accounts during the flow. The business customer’s Instagram account ID.
1749204838281942
<CUSTOMER_WABA_ID> (in waba_ids array)
Only included for multi-WABA flows. Array of the business customer’s WhatsApp Business account IDs.
524126980791429
<FLOW_FINISH_TYPE>
Indicates the customer successfully completed the flow.
Possible Values:
FINISH: Indicates successful completion of Cloud API flow.
FINISH_ONLY_WABA: Indicates user completed flow without a phone number.
FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING: Indicates user completed flow with a WhatsApp business app number.
FINISH_OBO_MIGRATION: Indicates user completed an on-behalf-of migration flow.
FINISH_GRANT_ONLY_API_ACCESS: Indicates user completed a grant-only API access flow.
ERROR: Indicates the user encountered an error during the flow.
FINISH
Abandoned flow structure:
{
  data: {
    current_step: '<CURRENT_STEP>',
  },
  type: 'WA_EMBEDDED_SIGNUP',
  event: 'CANCEL',
}
Placeholder	Description	Example value
<CURRENT_STEP>
Indicates which screen the business customer was viewing when they abandoned the flow. See Embedded Signup flow errors for a description of each step.
PHONE_NUMBER_SETUP
User reported errors:
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
Placeholder	Description	Example value
<ERROR_MESSAGE>
The error description text displayed to the business customer in the Embedded Signup flow. See Embedded Signup flow errors for a list of common errors.
Your verified name violates WhatsApp guidelines. Please edit your verified name and try again.
<ERROR_CODE>
Error code. Include this value if you contact support.
524126
<SESSION_ID>
Unique session ID generated by Embedded Signup. Include this ID if you contact support.
f34b51dab5e0498
<TIMESTAMP>
Unix timestamp indicating when the business customer used Embedded Signup to report the error. Include this value if you are contacting support.
1746041036
Parse this object on your server to extract and capture the customer’s phone number ID and WABA ID, or to determine which screen they abandoned. See Abandoned flow screens for a list of possible <CURRENT_STEP> values and the screens they correspond to.
Note that the try-catch statement in the code above has two statements that can be used for testing purposes:
console.log('message event: ', data); // remove after testing

console.log('message event: ', event.data); // remove after testing
These statements just dump the returned phone number and WABA IDs, or the abandoned screen string, to the JavaScript console. You can leave this code in place and keep the console open to easily see what gets returned when you are testing the flow, but you should remove them when you are done testing.
Response callback
Whenever a business customer successfully completes the Embedded Signup flow, Meta sends an exchangeable token code in a JavaScript response⁠ to the window that spawned the flow.
// Response callback
const fbLoginCallback = (response) => {
  if (response.authResponse) {
    const code = response.authResponse.code;
    console.log('response: ', code); // remove after testing
    // your code goes here
  } else {
    console.log('response: ', response); // remove after testing
    // your code goes here
  }
}
The callback function assigns the exchangeable token code to a code constant.
Add your own, custom code to the if-else statement that sends this code to your server so you can later exchange it for the customer’s business token when you onboard the business customer.
The exchangeable token code has a time-to-live of 30 seconds, so make sure you are able to exchange it for the customer’s business token before the code expires. If you are testing and just dumping the response to your JavaScript console, then manually exchanging the code using another app like Postman or your terminal with cURL, set up your token exchange query before you begin testing.
Note that the if-else statement in the code above has two statements that can be used for testing purposes:
console.log('response: ', code); // remove after testing

console.log('response: ', response); // remove after testing
These statements just dump the code or the raw response to the JavaScript console. You can leave this code in place and keep the console open to easily see what gets returned when you are testing the flow, but you should remove them when you are done testing.
Launch method and callback registration
This portion of the code defines a method which can be called by an onclick event that registers the response callback from the previous step and launches the Embedded Signup flow.
Add your configuration ID here.
// Launch method and callback registration
const launchWhatsAppSignup = () => {
  FB.login(fbLoginCallback, {
    config_id: '<CONFIGURATION_ID>', // your configuration ID goes here
    response_type: 'code',
    override_default_response_type: true,
    extras: {
      setup: {},
    }
  });
}
Launch button
This portion of the code defines a button that calls the launch method from the previous step when clicked by the business customer.
<!-- Launch button -->
<button onclick="launchWhatsAppSignup()" style="background-color: #1877f2; border: 0; border-radius: 4px; color: #fff; cursor: pointer; font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: bold; height: 40px; padding: 0 24px;">Login with Facebook</button>
Testing
Once you have completed all of the implementation steps above, you should be able to test the flow by simulating a business customer while using your own Meta credentials. Anyone who you have added as an admin or developer on your app (in the App Dashboard > App roles > Roles panel) can also begin testing the flow, using their own Meta credentials.
Onboarding business customers
Embedded Signup generates assets for your business customers, and grants your app access to those assets. However, you still need to make a series of API calls to fully onboard new business customers who have completed the flow.