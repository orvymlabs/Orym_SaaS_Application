[EmbeddedSignup] Message listener registered
page-6bf5cf28e2d5863c.js:1 Facebook SDK initialized with App ID: 3862862217342382
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)
page-6bf5cf28e2d5863c.js:1   Config ID: 2432311603846818
page-6bf5cf28e2d5863c.js:1   response_type: code | override_default_response_type: true | extras: {"setup":{},"sessionInfoVersion":3}
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] WINDOW MESSAGE RECEIVED
page-6bf5cf28e2d5863c.js:1   origin: https://www.facebook.com
page-6bf5cf28e2d5863c.js:1   dataType: string
page-6bf5cf28e2d5863c.js:1   isJSON: false
page-6bf5cf28e2d5863c.js:1   containsOAuthCode: true
page-6bf5cf28e2d5863c.js:1   containsWA_EMBEDDED_SIGNUP: false
page-6bf5cf28e2d5863c.js:1   containsSessionInfo: false
page-6bf5cf28e2d5863c.js:1   waba_id present: false
page-6bf5cf28e2d5863c.js:1   phone_number_id present: false
page-6bf5cf28e2d5863c.js:1   business_id present: false
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] code received, waiting briefly for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] LOGIN_CODE_RECEIVED (length: 451 )
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] WA_EMBEDDED_SIGNUP session event not received - proceeding with code-only (backend server-side resolution)
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] READY_FOR_BACKEND_EXCHANGE
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] BACKEND_EXCHANGE_STARTED
page-6bf5cf28e2d5863c.js:1   Code length: 451
page-6bf5cf28e2d5863c.js:1   waba_id: not provided
page-6bf5cf28e2d5863c.js:1   phone_number_id: not provided
page-6bf5cf28e2d5863c.js:1   business_id: not provided
page-6bf5cf28e2d5863c.js:1   Note: exchangeable code expires in 30 seconds and is single-use
layout-818c5b84e3a33af1.js:1  POST https://orym-saas-application.onrender.com/api/integrations/meta/oauth/callback 400 (Bad Request)
o @ layout-818c5b84e3a33af1.js:1
s @ layout-818c5b84e3a33af1.js:1
et @ page-6bf5cf28e2d5863c.js:1
Q @ page-6bf5cf28e2d5863c.js:1
(anonymous) @ page-6bf5cf28e2d5863c.js:1
setTimeout
Z @ page-6bf5cf28e2d5863c.js:1
e @ page-6bf5cf28e2d5863c.js:1
page-6bf5cf28e2d5863c.js:1 [EmbeddedSignup] OAuth callback error: Error: Невозможно загрузить URL: Домен этого URL не включен в список доменов приложения. Чтобы загрузить этот URL, добавьте все домены и поддомены своего приложения в поле «Домены приложения» в настройках вашего приложения.
    at o (layout-818c5b84e3a33af1.js:1:24162)
    at async et (page-6bf5cf28e2d5863c.js:1:11807)