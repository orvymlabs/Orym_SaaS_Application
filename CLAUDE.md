STOP making assumptions about redirect_uri.

Do not make any more fixes until you identify the exact root cause.

Current situation:

- Existing WhatsApp Cloud API bot using the SAME Meta App works perfectly.
- App ID, App Secret, Webhook and WhatsApp product are already working.
- Embedded Signup opens successfully.
- User completes authorization successfully.
- Authorization code is returned successfully (length ~451).
- Failure happens ONLY during code exchange.

Browser error:

Error validating verification code.
Please make sure your redirect_uri is identical to the one you used in the OAuth dialog request.

Your task is NOT to guess.

I want you to debug this properly.

Please do the following:

1. Print the EXACT Graph API request being sent to:
https://graph.facebook.com/v21.0/oauth/access_token

Show every parameter.

2. Print the FULL Graph API response.

Do NOT truncate it.

Include:
- error.code
- error_subcode
- error_user_title
- error_user_msg
- fbtrace_id

3. Compare my implementation with Meta's OFFICIAL WhatsApp Embedded Signup documentation.

Do not compare with generic Facebook OAuth.

4. Verify whether FB.login() with config_id requires:
- redirect_uri omitted
- redirect_uri=""
- redirect_uri=https://...

using Meta documentation only.

5. Verify whether the OAuth endpoint itself is correct for Embedded Signup.

6. Verify that my Configuration ID is actually a WhatsApp Embedded Signup configuration and not a generic Facebook Login for Business configuration.

7. Check whether Embedded Signup returns an authorization code that should be exchanged differently than standard Facebook Login.

8. Add logging around EVERY Graph API call.

Print:

Request URL

HTTP Method

Query Parameters

Response Status

Complete Response Body

9. If you discover the root cause, explain WHY it happens before changing code.

Do not patch blindly.

I want root-cause analysis, not trial-and-error.

Search Meta's official documentation and verify whether the OAuth exchange flow I'm using is compatible with WhatsApp Embedded Signup (Facebook Login for Business) in Graph API v21.0.

If not, replace it with the official implementation from Meta documentation.