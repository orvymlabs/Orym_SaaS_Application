Fix ONLY the current WhatsApp Embedded Signup issue. DO NOT modify, refactor, redesign, or touch any other part of the ORVYM SaaS platform.

This is a targeted bug fix.

## CURRENT ISSUE

Production logs:

Facebook SDK initialized with App ID:
3862862217342382

Embedded Signup launches:

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login (JS SDK)
App ID: 3862862217342382
Config ID: 2432311603846818

Meta message event:

[EmbeddedSignup] message event received from https://www.facebook.com | event: SDK_QUERY_STRING

Exchangeable code is successfully received:

[EmbeddedSignup] code received: yes (length 451)

FB.login also returns:

[EmbeddedSignup] FB.login response status: connected

BUT:

[EmbeddedSignup] waba_id: MISSING
[EmbeddedSignup] phone_number_id: MISSING
[EmbeddedSignup] business_id: MISSING

Also, the logs show that:

[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login (JS SDK)

is being triggered more than once.

## YOUR TASK

Fix ONLY these Embedded Signup problems:

1. Correctly parse the Meta `SDK_QUERY_STRING` message payload so that the required WhatsApp information is extracted correctly.

2. Keep the existing exchangeable code flow working exactly as it currently does.

3. Fix the duplicate `FB.login()` / duplicate Embedded Signup launch.

4. Make sure the code is processed only once per signup attempt.

5. Make sure the existing backend exchange call continues to receive the correct exchangeable code.

6. If WABA ID, phone number ID, or business ID are already returned somewhere in the existing Meta response, correctly extract them. Do not hardcode them.

7. If the current code is reading the wrong property/path from `event.data`, correct only that parsing logic.

8. Add safe debugging logs if needed to identify the actual payload structure.

## VERY IMPORTANT — DO NOT TOUCH ANYTHING ELSE

Do NOT modify:

* ORVYM dashboard
* UI design
* authentication
* user system
* tenant system
* database architecture
* database models
* WhatsApp webhook system
* WhatsApp messaging logic
* AI system
* chatbot
* inbox
* templates
* campaigns
* analytics
* subscription system
* billing
* existing API architecture
* existing backend services unrelated to Embedded Signup
* existing Meta configuration unrelated to this issue
* any working feature

Do NOT refactor unrelated code.

Do NOT upgrade dependencies.

Do NOT change the App ID.

Do NOT change the Config ID.

App ID:
3862862217342382

Config ID:
2432311603846818

## DUPLICATE LAUNCH FIX

Find exactly why `FB.login()` is being called twice.

Inspect only the Embedded Signup implementation for:

* duplicate onClick
* duplicate useEffect
* duplicate event listener
* component remount
* callback triggering signup again
* signup handler being called multiple times

Fix it with the smallest possible change.

Expected behavior:

ONE click
→ ONE FB.login()
→ ONE Embedded Signup
→ ONE code received
→ ONE backend exchange

Do not permanently disable reconnect/retry.

## PAYLOAD DEBUGGING

Before changing the parser, inspect the actual `SDK_QUERY_STRING` payload.

Log safely:

* event.origin
* typeof event.data
* event.data
* parsed event.data
* relevant nested properties

Determine the actual location/format of:

* code
* waba_id
* phone_number_id
* business_id

Do not assume they are directly:

event.data.waba_id
event.data.phone_number_id
event.data.business_id

If the data is a query string, parse it correctly.

If it is JSON, parse it correctly.

If it is nested, access the correct nested fields.

Do not invent values.

## PRESERVE THE CURRENT WORKING CODE

The following is already working and MUST remain working:

* Facebook SDK initialization
* App ID
* Config ID
* FB.login
* Embedded Signup opening
* Meta message event
* exchangeable authorization code reception
* existing backend code exchange

Only fix the broken parsing and duplicate triggering.

## SUCCESS CONDITION

The final logs should no longer incorrectly show:

waba_id: MISSING
phone_number_id: MISSING
business_id: MISSING

if those values are actually available in the Meta response.

And one signup attempt must not produce multiple:

Launching WhatsApp Embedded Signup via FB.login

logs.

## IMPORTANT

Do not solve this by hiding the logs.

Do not simply remove the `MISSING` messages.

Actually fix the data extraction.

Do not fake IDs.

Do not hardcode IDs.

Do not rewrite the whole integration.

Make the SMALLEST SAFE CODE CHANGES necessary to make the existing Embedded Signup implementation work correctly.

After fixing it, report ONLY:

1. Root cause
2. Files changed
3. Exact fix made
4. Confirmation that no unrelated ORVYM functionality was modified
5. Any Meta dashboard change required, if absolutely necessary
