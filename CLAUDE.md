FIX THE CURRENT WHATSAPP EMBEDDED SIGNUP FLOW.

CURRENT BUG:
The frontend receives the Meta exchangeable authorization code successfully:

[EmbeddedSignup] exchangeable code received via FB.login callback (length: 451)

BUT THEN IT DOES:

"Exchange skipped - session asset IDs not received yet"

because waba_id and phone_number_id have not arrived yet.

THIS IS WRONG.

DO NOT SKIP TOKEN EXCHANGE JUST BECAUSE waba_id / phone_number_id HAVE NOT ARRIVED YET.

IMPLEMENT THE OFFICIAL EMBEDDED SIGNUP SESSION FLOW CORRECTLY:

1. Register window.message listener BEFORE calling FB.login.

2. Listen for Meta messages where:
   event.origin is Facebook/Meta
   AND parsed message.type === "WA_EMBEDDED_SIGNUP".

3. Handle the completion event:
   event.event === "FINISH"

4. Extract:
   data.data.waba_id
   data.data.phone_number_id
   data.data.business_id

5. Store these IDs in React/state/ref immediately.

6. The FB.login callback receives:
   response.authResponse.code

   Store this code immediately.

7. DO NOT require the IDs before accepting/storing the code.

8. Implement a synchronization function such as:

   maybeCompleteEmbeddedSignup()

   It should proceed when:
   - authorization code exists
   - and required session information is available

   Do NOT exchange the same code more than once.

9. CRITICAL:
   Do not poll the backend repeatedly.
   Do not retry the same Meta authorization code.
   Do not send the same code multiple times.
   The code is single-use and short-lived.

10. Once the code and required session data are available, send ONE backend request:

POST /api/integrations/meta/oauth/callback

Payload:

{
  code,
  redirect_uri,
  waba_id,
  phone_number_id,
  business_id
}

11. Backend must perform the token exchange exactly once.

12. Backend must NOT attempt WABA discovery through:
   GET /me/businesses

   if the Embedded Signup session already supplied waba_id.

13. Use the supplied waba_id and phone_number_id directly for the next provisioning steps.

14. Do NOT use /me/businesses as the primary WABA discovery mechanism because this was previously causing:

(#100) Missing Permission

15. Backend flow must become:

   authorization code
        ↓
   exchange code for access token
        ↓
   validate/debug token and scopes
        ↓
   use supplied waba_id
        ↓
   use supplied phone_number_id
        ↓
   verify/access WABA
        ↓
   subscribe app to WABA webhooks
        ↓
   register/configure phone number if required
        ↓
   save WABA ID + phone number ID + token securely
        ↓
   return success to frontend

16. IMPORTANT RACE-CONDITION HANDLING:

If the FB.login callback fires first:
   save code and wait briefly for the WA_EMBEDDED_SIGNUP FINISH message.

If the WA_EMBEDDED_SIGNUP FINISH message fires first:
   save waba_id / phone_number_id / business_id and wait for the code.

When both are available:
   call backend exactly once.

17. Add a hard timeout of approximately 10-15 seconds for waiting for the missing counterpart.

18. If the FINISH event never arrives, show a clear onboarding error instead of silently skipping the exchange.

19. Log these events:

   [EmbeddedSignup] LOGIN_CODE_RECEIVED
   [EmbeddedSignup] SESSION_FINISH_RECEIVED
   [EmbeddedSignup] WABA_ID_RECEIVED
   [EmbeddedSignup] PHONE_NUMBER_ID_RECEIVED
   [EmbeddedSignup] BUSINESS_ID_RECEIVED
   [EmbeddedSignup] READY_FOR_BACKEND_EXCHANGE
   [EmbeddedSignup] BACKEND_EXCHANGE_STARTED
   [EmbeddedSignup] BACKEND_EXCHANGE_SUCCESS
   [EmbeddedSignup] EMBEDDED_SIGNUP_COMPLETE

20. NEVER log:
   app_secret
   access_token
   full authorization code

21. Prevent duplicate execution using a ref/lock such as:
   exchangeStartedRef.current = true

22. IMPORTANT:
   Remove the current logic that says:

   "Exchange skipped - session asset IDs not received yet"

   The absence of IDs at the exact moment the code callback fires must NOT cause the code to be discarded.

23. Keep the Meta launch configuration:

   FB.login(fbLoginCallback, {
     config_id: "2432311603846818",
     response_type: "code",
     override_default_response_type: true,
     extras: {
       setup: {}
     }
   });

24. Do not introduce another OAuth flow.
   Do not switch back to a normal Facebook OAuth implementation.
   Keep this as WhatsApp Embedded Signup / Facebook Login for Business.

25. BACKEND MUST ACCEPT the IDs supplied by Embedded Signup and must not unnecessarily discover the customer's WABA through /me/businesses.

26. IMPORTANT FOR THE PREVIOUS REDIRECT_URI ERROR:

Do not change redirect_uri randomly.
Keep one canonical production value everywhere:

https://apps.orvym.com/dashboard/integrations/

Use the exact same value wherever the current OAuth/configuration flow requires it.

27. AFTER IMPLEMENTATION, TEST A FRESH EMBEDDED SIGNUP SESSION.

Do NOT reuse an old 451-character authorization code.

EXPECTED CONSOLE FLOW:

[EmbeddedSignup] Launching WhatsApp Embedded Signup
[EmbeddedSignup] LOGIN_CODE_RECEIVED
[EmbeddedSignup] SESSION_FINISH_RECEIVED
[EmbeddedSignup] WABA_ID_RECEIVED
[EmbeddedSignup] PHONE_NUMBER_ID_RECEIVED
[EmbeddedSignup] READY_FOR_BACKEND_EXCHANGE
[EmbeddedSignup] BACKEND_EXCHANGE_STARTED
[EmbeddedSignup] BACKEND_EXCHANGE_SUCCESS
[EmbeddedSignup] EMBEDDED_SIGNUP_COMPLETE

EXPECTED RESULT:

The frontend must no longer show:

"Exchange skipped - session asset IDs not received yet"

The backend must no longer fail at:

/me/businesses

with:

(#100) Missing Permission

The final result should be that the customer's WhatsApp Business Account and phone number are successfully connected and stored in the user's integration record.

DO NOT mark the implementation complete until a fresh production Embedded Signup test reaches EMBEDDED_SIGNUP_COMPLETE and the connected WABA/phone number is visible in the dashboard.