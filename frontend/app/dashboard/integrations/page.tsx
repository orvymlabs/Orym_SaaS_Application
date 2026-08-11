"use client";
import { useEffect, useRef, useState } from "react";
import { apiGet, apiPost, apiPatch } from "@/lib/api";
import { useToast } from "@/components/ui";
import { useTheme } from "@/lib/useTheme";

interface IntegrationData {
  id: number;
  bot_id: number;
  phone_number_id: string | null;
  whatsapp_number: string | null;
  verify_token: string;
  woocommerce_url: string | null;
  wp_base_url: string | null;
  business_type: string;
  has_whatsapp_token: boolean;
  whatsapp_token_preview: string;
  has_woo_keys: boolean;
  woo_products_cached: boolean;
  woo_categories_cached: any[];
  woo_products_count: number;
  webhook_url: string | null;
}

export default function IntegrationsPage() {
  const [integ, setInteg] = useState<IntegrationData | null>(null);
  const [userPlan, setUserPlan] = useState<string>("free");
  const [whatsappForm, setWhatsappForm] = useState({
    whatsapp_token: "",
    phone_number_id: "",
    whatsapp_number: "",
    verify_token: "",
  });
  const [metaConfig, setMetaConfig] = useState<{ app_id: string; config_id: string } | null>(null);
  const [facebookSdkReady, setFacebookSdkReady] = useState(false);
  const [connectingWhatsApp, setConnectingWhatsApp] = useState(false);
  const [disconnectingWhatsApp, setDisconnectingWhatsApp] = useState(false);
  // True while the single-use authorization code is being exchanged. The
  // Connect button is disabled for the whole exchange so the same code can
  // never be submitted twice from the UI.
  const [isExchangeInProgress, setIsExchangeInProgress] = useState(false);

  const generateVerifyToken = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let token = 'orvym';
    for (let i = 0; i < 32; i++) {
      token += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return token;
  };

  const handleGenerateAndSave = async () => {
    const newToken = generateVerifyToken();
    setWhatsappForm(prev => ({ ...prev, verify_token: newToken }));
    setSavingWhatsApp(true);
    try {
      await apiPatch("/api/integrations/me", { verify_token: newToken });
      showToast("Token updated successfully", "success");
      apiGet<IntegrationData>("/api/integrations/me").then(setInteg).catch(console.error);
    } catch (err: any) {
      showToast("Error updating token: " + err.message, "error");
    } finally {
      setSavingWhatsApp(false);
    }
  };

  const [phoneNumber, setPhoneNumber] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("+1");
  const [ecommerceForm, setEcommerceForm] = useState({
    website_url: "",
    consumer_key: "",
    consumer_secret: "",
  });
  const [integrationType, setIntegrationType] = useState<"product" | "service">("product");

  const countries = [
    { code: "+1", name: "United States/Canada", flag: "🇺🇸" },
    { code: "+44", name: "United Kingdom", flag: "🇬🇧" },
    { code: "+92", name: "Pakistan", flag: "🇵🇰" },
    { code: "+91", name: "India", flag: "🇮🇳" },
    { code: "+971", name: "UAE", flag: "🇦🇪" },
    { code: "+966", name: "Saudi Arabia", flag: "🇸🇦" },
    { code: "+61", name: "Australia", flag: "🇦🇺" },
    { code: "+49", name: "Germany", flag: "🇩🇪" },
    { code: "+33", name: "France", flag: "🇫🇷" },
    { code: "+86", name: "China", flag: "🇨🇳" },
    { code: "+81", name: "Japan", flag: "🇯🇵" },
    { code: "+82", name: "South Korea", flag: "🇰🇷" },
    { code: "+55", name: "Brazil", flag: "🇧🇷" },
    { code: "+52", name: "Mexico", flag: "🇲🇽" },
    { code: "+27", name: "South Africa", flag: "🇿🇦" },
  ];
  const [savingWhatsApp, setSavingWhatsApp] = useState(false);
  const [savingEcommerce, setSavingEcommerce] = useState(false);
  const [fetchingProducts, setFetchingProducts] = useState(false);
  const [buttonCode, setButtonCode] = useState("");
  const [activeTab, setActiveTab] = useState<"whatsapp" | "website" | "button">("whatsapp");
  const { showToast, ToastContainer } = useToast();
  const { isDark } = useTheme();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? 'https://orym-saas-application.onrender.com' : '');
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || (typeof window !== 'undefined' ? window.location.origin : 'https://apps.orvym.com');

  // Canonical production redirect URI. Meta binds the authorization code to the
  // exact redirect_uri used in the OAuth dialog request, so the code exchange
  // MUST send this exact value (never window.location.origin, never a
  // dynamically-built URI, never a value without the trailing slash). The
  // frontend and backend use exactly the same constant.
  const CANONICAL_REDIRECT_URI = "https://apps.orvym.com/dashboard/integrations/";

  // Official Meta Embedded Signup flow (JS SDK): FB.login() opens the Embedded
  // Signup in a centered popup window and the SaaS page stays open behind it.
  // On completion Meta:
  //   1. posts a WA_EMBEDDED_SIGNUP session message to THIS window (the window
  //      that spawned the flow) carrying the customer's asset IDs
  //      (waba_id, phone_number_id, business_id) - captured below.
  //   2. delivers the exchangeable code to the FB.login callback
  //      (response.authResponse.code).
  // The code + asset IDs are sent to the backend. The single-use code is
  // exchanged EXACTLY ONCE - a one-time guard (completingRef) locks the
  // exchange the moment it starts and the code is cleared before it is sent,
  // so it can never be submitted to the backend a second time.
  const signupCodeRef = useRef<string | null>(null);
  const signupDataRef = useRef<{ waba_id?: string; phone_number_id?: string; business_id?: string }>({});
  const completingRef = useRef(false);
  // Stale-closure safety (Part 12 of the spec): the message listener is
  // registered in a mount-once useEffect, so any state it reads must be
  // mirrored in refs. The Config ID is stored here when it loads so the
  // listener/timeout diagnostics never read a stale null from the first render.
  const configIdRef = useRef<string | null>(null);
  // Diagnostic accumulation for the current Embedded Signup attempt. Every
  // window message origin/type observed during an active attempt is recorded
  // here (never secrets - just origin + type + parsed event name) so the
  // timeout handler can report exactly what Meta did or did not send.
  const messageDiagnosticsRef = useRef<Array<{ origin: string; type: string; event?: string }>>([]);
  // Synchronous guard against duplicate launches (e.g. a fast double-click
  // before React re-renders the disabled state). It is cleared again when the
  // flow finishes, cancels or errors, so reconnect/retry keeps working.
  const launchingRef = useRef(false);
  // Short wait timeout for the WA_EMBEDDED_SIGNUP session counterpart. The code
  // and the session message can arrive in either order; if one half lands
  // without the other, we wait briefly for the missing piece. Meta delivers the
  // session event at the same time as the code, so ~20s is generous. If the
  // FINISH session event does not arrive within that window the flow does NOT
  // fail - the code is handed to the backend alone and the backend resolves the
  // WABA ID / phone number ID server-side using the documented Meta fallback.
  const sessionWaitTimeoutRef = useRef<number | null>(null);

  const clearSessionWaitTimeout = () => {
    if (sessionWaitTimeoutRef.current != null) {
      window.clearTimeout(sessionWaitTimeoutRef.current);
      sessionWaitTimeoutRef.current = null;
    }
  };

  // Complete the connection exactly once, as soon as BOTH the single-use
  // exchangeable code AND the WA_EMBEDDED_SIGNUP session asset IDs are
  // available. The code and the session message can arrive in any order; this
  // single owner is called from both paths and only fires when both are
  // present. When the session event is delayed/unavailable (only the code
  // arrived), a short wait gives the session event a chance to land and then
  // the code is handed to the backend anyway - the backend resolves the WABA
  // ID and phone number ID server-side using the documented Meta fallback
  // (/debug_token granular_scopes target_ids + the WABA phone_numbers edge).
  // The code is NEVER discarded and NEVER sent to the backend more than once
  // (the one-time completingRef guard locks the exchange the moment it starts
  // and the code is cleared before it is sent).
  const startBackendExchange = (code: string) => {
    if (completingRef.current) return;
    clearSessionWaitTimeout();
    completingRef.current = true;
    setIsExchangeInProgress(true);
    console.log('[EmbeddedSignup] READY_FOR_BACKEND_EXCHANGE');
    signupCodeRef.current = null; // clear code immediately after capture
    handleMetaOAuthCallback(code, { ...signupDataRef.current });
  };

  const completeEmbeddedSignup = () => {
    if (completingRef.current) return;
    const code = signupCodeRef.current;
    if (!code) return;
    const { waba_id, phone_number_id } = signupDataRef.current;
    if (!waba_id || !phone_number_id) {
      // The code arrived but the WA_EMBEDDED_SIGNUP FINISH session message has
      // not delivered the asset IDs yet. Keep the code (it is NOT discarded)
      // and start a single short wait for the session event (Meta delivers it
      // at the same time as the code, so ~20s is generous). If the IDs still
      // have not arrived when it fires, proceed with the code ALONE - the
      // backend resolves WABA ID / phone number ID server-side via the
      // documented Meta fallback instead of failing the onboarding.
      if (sessionWaitTimeoutRef.current == null) {
        console.log('[EmbeddedSignup] code received, waiting briefly for WA_EMBEDDED_SIGNUP session asset IDs (waba_id / phone_number_id)');
        sessionWaitTimeoutRef.current = window.setTimeout(() => {
          sessionWaitTimeoutRef.current = null;
          // Session event did not deliver the asset IDs in time. Do NOT fail -
          // hand the code to the backend which resolves the IDs server-side
          // (the complete recovery path).
          if (!signupDataRef.current.waba_id || !signupDataRef.current.phone_number_id) {
            console.log('[EmbeddedSignup] WA_EMBEDDED_SIGNUP session event not received - proceeding with code-only (backend server-side resolution)');
            startBackendExchange(code);
          }
        }, 20000);
      }
      return;
    }
    startBackendExchange(code);
  };

  // Load and initialize the Facebook JS SDK (Official Meta Code). fbAsyncInit
  // must be assigned BEFORE the SDK script finishes loading so Meta's SDK runs
  // FB.init with the correct App ID once ready.
  const loadFacebookSDK = (appId: string) => {
    if (typeof window === 'undefined') return;

    // SDK initialization - Official Meta Code
    (window as any).fbAsyncInit = function () {
      if (window.FB) {
        window.FB.init({
          appId,
          cookie: true,
          autoLogAppEvents: true,
          xfbml: true,
          version: 'v26.0', // Latest Graph API version (per current Meta docs)
        });
        setFacebookSdkReady(true);
        console.log('Facebook SDK initialized with App ID:', appId);
      }
    };

    if (document.getElementById('facebook-jssdk')) {
      // SDK script is already present (loading or loaded). If it has finished
      // loading, fbAsyncInit has already fired - run it now so FB.init runs.
      if (window.FB) {
        (window as any).fbAsyncInit();
      }
    } else {
      // SDK loading - Official Meta Code
      const script = document.createElement('script');
      script.id = 'facebook-jssdk';
      script.src = 'https://connect.facebook.net/en_US/sdk.js';
      script.async = true;
      script.defer = true;
      script.crossOrigin = 'anonymous';
      document.body.appendChild(script);
    }
  };

  useEffect(() => {
    // Fetch user plan
    apiGet<any>("/api/auth/usage").then((data) => {
      if (data?.plan) setUserPlan(data.plan);
    }).catch(console.error);

    // Fetch Meta configuration
    apiGet<{ app_id: string; config_id: string }>("/api/integrations/meta/config")
      .then(config => {
        setMetaConfig(config);
        configIdRef.current = config?.config_id || null;
        // Load + initialize the Facebook JS SDK after the App ID is known.
        if (typeof window !== 'undefined' && config) {
          loadFacebookSDK(config.app_id);
        }
      })
      .catch(err => {
        console.warn("Meta Embedded Signup not configured:", err);
      });

    // Session logging message event listener - Official Meta Code.
    // WhatsApp Embedded Signup posts a WA_EMBEDDED_SIGNUP message to this
    // window when the user finishes (FINISH / FINISH_*), cancels (CANCEL) or
    // hits an error (ERROR). On FINISH the event data is (Meta's documented
    // format):
    //   {
    //     type: "WA_EMBEDDED_SIGNUP",
    //     event: "FINISH",
    //     data: { phone_number_id, waba_id, business_id, ... }
    //   }
    // The asset IDs are captured here when provided (never fabricated); the
    // exchangeable code itself is delivered via the FB.login callback.
    //
    // This listener is registered ONCE on mount - always BEFORE any FB.login()
    // call (which is only ever invoked from a user click) - and stays alive for
    // the whole signup session. It logs every window message observed while an
    // attempt is active (origin + type + parsed event name, NEVER secrets) so a
    // missing FINISH can be diagnosed precisely instead of guessed.
    const handleEmbeddedSignupMessage = (event: MessageEvent) => {
      const attemptActive = !!launchingRef.current;
      const origin = event.origin || 'unknown';

      // SAFE FACEBOOK-ORIGIN VALIDATION (Part 2 of the spec). Accept the
      // production origin https://www.facebook.com and any legitimate
      // facebook.com subdomain. Do NOT accept arbitrary origins. Rejected
      // origins are logged (never silently dropped) so we can tell whether the
      // SDK is posting from an unexpected origin.
      const isFacebookOrigin =
        origin === 'https://www.facebook.com' ||
        origin === 'https://facebook.com' ||
        origin === 'https://business.facebook.com' ||
        origin.endsWith('.facebook.com');

      if (!isFacebookOrigin) {
        if (attemptActive) {
          console.log('[EmbeddedSignup] Ignored message origin:', origin);
          messageDiagnosticsRef.current.push({ origin, type: 'ignored-origin' });
        }
        return;
      }

      // LOG EVERY MESSAGE DURING AN ACTIVE ATTEMPT (Part 3 of the spec) using
      // ONLY safe metadata - never the raw message body. The OAuth redirect
      // message carries the exchangeable code (code=...) in its query string,
      // so logging rawData would leak the single-use code; per the spec only
      // origin, data type and presence booleans are logged.
      if (attemptActive) {
        console.log('[EmbeddedSignup] WINDOW MESSAGE RECEIVED');
        console.log('  origin:', origin);
        console.log('  dataType:', typeof event.data);
        const rawForMeta = typeof event.data === 'string' ? event.data : (event.data ? JSON.stringify(event.data) : '');
        const isJSON = (() => {
          if (typeof event.data !== 'string') return typeof event.data === 'object';
          try { JSON.parse(event.data); return true; } catch { return false; }
        })();
        console.log('  isJSON:', isJSON);
        console.log('  containsOAuthCode:', /(?:[?&]code=)([^&\s]+)/.test(rawForMeta) || !!event.data?.code || !!event.data?.authResponse?.code);
        console.log('  containsWA_EMBEDDED_SIGNUP:', rawForMeta.includes('WA_EMBEDDED_SIGNUP') || event.data?.type === 'WA_EMBEDDED_SIGNUP' || event.data?.event === 'WA_EMBEDDED_SIGNUP');
        console.log('  containsSessionInfo:', !!event.data?.data || rawForMeta.includes('"data"'));
        console.log('  waba_id present:', !!event.data?.waba_id || !!event.data?.data?.waba_id || rawForMeta.includes('"waba_id"'));
        console.log('  phone_number_id present:', !!event.data?.phone_number_id || !!event.data?.data?.phone_number_id || rawForMeta.includes('"phone_number_id"'));
        console.log('  business_id present:', !!event.data?.business_id || !!event.data?.data?.business_id || rawForMeta.includes('"business_id"'));
      }

      // event.data may be a JSON string (Meta's documented format) or, in some
      // environments, already an object. Handle both safely.
      let data: any = event.data;
      if (typeof data === 'string') {
        try {
          data = JSON.parse(data);
        } catch {
          // Do NOT discard non-JSON messages (Part 4/5 of the spec). The OAuth
          // redirect-back message from oauth.facebook.com is a URL-query-string
          // like cb=...&domain=apps.orvym.com&...&code=... - NOT JSON. Extract
          // the exchangeable code from it as a parallel/fallback path to the
          // FB.login callback (the code value is never logged).
          if (attemptActive) {
            messageDiagnosticsRef.current.push({ origin, type: 'non-json-string' });
            const raw = event.data as string;
            const codeMatch = /(?:[?&]code=)([^&\s]+)/.exec(raw);
            if (codeMatch && codeMatch[1]) {
              let codeVal = codeMatch[1];
              try { codeVal = decodeURIComponent(codeVal); } catch { /* keep raw */ }
              console.log('[EmbeddedSignup] OAuth code detected in non-JSON redirect message (fallback path)');
              if (codeVal && !signupCodeRef.current) {
                signupCodeRef.current = codeVal;
                completeEmbeddedSignup();
              }
            } else {
              console.log('[EmbeddedSignup] PARSED MESSAGE: non-JSON string (no code param) - ignored');
            }
          }
          return;
        }
      }

      if (data && typeof data === 'object' && attemptActive) {
        const dataKeys = data.data && typeof data.data === 'object'
          ? Object.keys(data.data)
          : [];
        console.log('[EmbeddedSignup] PARSED MESSAGE');
        console.log('  type:', data.type);
        console.log('  event:', data.event);
        console.log('  version:', data.version);
        console.log('  data keys:', dataKeys.join(', ') || '(none)');
      }

      // Detect the Embedded Signup session message (Part 8 of the spec). The
      // documented format uses data.type === 'WA_EMBEDDED_SIGNUP' with the event
      // name in data.event, but some Meta payloads mark the message type in the
      // event field instead, and the signup envelope can occasionally arrive
      // nested one level down (data.data) - accept ALL of these so no official
      // session event is discarded, while still rejecting arbitrary messages.
      let signup: any = data;
      if (
        data &&
        typeof data === 'object' &&
        data.data &&
        typeof data.data === 'object' &&
        (data.data.type === 'WA_EMBEDDED_SIGNUP' || data.data.event === 'WA_EMBEDDED_SIGNUP')
      ) {
        signup = data.data;
      }

      const isSignupMessage =
        !!signup &&
        typeof signup === 'object' &&
        (signup.type === 'WA_EMBEDDED_SIGNUP' || signup.event === 'WA_EMBEDDED_SIGNUP');

      if (!isSignupMessage) {
        if (attemptActive) {
          console.log('[EmbeddedSignup] Ignored message (not WA_EMBEDDED_SIGNUP). type:', data?.type || 'undefined', 'event:', data?.event || 'undefined');
          messageDiagnosticsRef.current.push({ origin, type: data?.type || 'non-wa-embedded-signup' });
        }
        return;
      }

      // Collect every container that may hold the session payload. Meta's
      // documented FINISH format places the asset IDs directly on the data key:
      //   { data: { waba_id, phone_number_id, business_id }, type, event }
      // but real payloads have also been observed with the asset IDs nested one
      // level deeper (data.data.data) or directly on the envelope. All
      // candidates are searched and merged so no legitimate session event is
      // ever dropped because of its nesting depth.
      const payloadCandidates: any[] = [];
      if (signup.data && typeof signup.data === 'object') {
        payloadCandidates.push(signup.data);
        if (signup.data.data && typeof signup.data.data === 'object') {
          payloadCandidates.push(signup.data.data);
        }
      }
      if (signup !== data && data && typeof data === 'object') {
        payloadCandidates.push(data);
      }
      payloadCandidates.push(signup);

      const sessionPayload: any = {};
      for (const candidate of payloadCandidates) {
        if (!candidate || typeof candidate !== 'object') continue;
        for (const field of ['waba_id', 'phone_number_id', 'business_id', 'waba_ids', 'error_message', 'error_code', 'current_step', 'session_id', 'timestamp']) {
          if (sessionPayload[field] === undefined && candidate[field] !== undefined) {
            sessionPayload[field] = candidate[field];
          }
        }
      }

      // Event name: normally signup.event is FINISH / CANCEL / ERROR. When the
      // event field itself is the WA_EMBEDDED_SIGNUP type marker, treat a
      // payload carrying asset IDs as FINISH and one carrying an error_message
      // as ERROR - never silently drop the session.
      let eventName = String(signup.event || 'UNKNOWN');
      if (eventName === 'WA_EMBEDDED_SIGNUP') {
        const hasAssets = !!(sessionPayload.waba_id || sessionPayload.phone_number_id || sessionPayload.waba_ids || sessionPayload.business_id);
        eventName = hasAssets ? 'FINISH' : (sessionPayload.error_message ? 'ERROR' : 'UNKNOWN');
      }
      const dataObj = sessionPayload;

      if (attemptActive) {
        messageDiagnosticsRef.current.push({ origin, type: 'WA_EMBEDDED_SIGNUP', event: eventName });
      }
      console.log('[EmbeddedSignup] WA_EMBEDDED_SIGNUP EVENT RECEIVED');
      console.log('  event:', eventName);
      console.log('  version:', signup.version);

      // Safe session-event diagnostics (never logs codes/tokens/secrets).
      const wabaReceived = !!sessionPayload.waba_id ||
        (Array.isArray(sessionPayload.waba_ids) && sessionPayload.waba_ids.length > 0);
      console.log('[EmbeddedSignup] SESSION EVENT RECEIVED');
      console.log('  event:', eventName);
      console.log('  sessionInfoVersion: 3');
      console.log('  waba_id:', wabaReceived ? 'received' : 'missing');
      console.log('  phone_number_id:', sessionPayload.phone_number_id ? 'received' : 'missing');
      console.log('  business_id:', sessionPayload.business_id ? 'received' : 'missing');
      console.log('  origin:', origin);

      // CANCEL - abandoned flow (capture current_step) or user-reported error
      // (capture error_message, error_code, session_id, timestamp).
      if (eventName === 'CANCEL') {
        console.log('[EmbeddedSignup] User cancelled Embedded Signup');
        console.log('  current_step:', dataObj.current_step || 'unknown');
        const errorMessage = dataObj.error_message;
        const errorCode = dataObj.error_code;
        if (errorMessage || errorCode) {
          console.log('[EmbeddedSignup] Flow error reported:', {
            error_message: errorMessage,
            error_code: errorCode,
            session_id: dataObj.session_id,
            timestamp: dataObj.timestamp,
          });
          clearSessionWaitTimeout();
          launchingRef.current = false;
          setIsExchangeInProgress(false);
          setConnectingWhatsApp(false);
          showToast(
            "WhatsApp setup failed: " + (errorMessage || "An error occurred during WhatsApp setup"),
            "error"
          );
        } else {
          clearSessionWaitTimeout();
          launchingRef.current = false;
          setIsExchangeInProgress(false);
          setConnectingWhatsApp(false);
          showToast("WhatsApp signup was cancelled. No changes were made.", "info");
        }
        return;
      }

      // ERROR - customer encountered an error during onboarding.
      if (eventName === 'ERROR') {
        const errorMessage = dataObj.error_message;
        const errorCode = dataObj.error_code;
        console.log('[EmbeddedSignup] Meta Embedded Signup ERROR');
        console.log('  error_message:', errorMessage);
        console.log('  error_code:', errorCode);
        console.log('  current_step:', dataObj.current_step || 'unknown');
        clearSessionWaitTimeout();
        launchingRef.current = false;
        setIsExchangeInProgress(false);
        setConnectingWhatsApp(false);
        showToast(
          "WhatsApp setup failed: " + (errorMessage || "An error occurred during WhatsApp setup"),
          "error"
        );
        return;
      }

      // Successful flow finish types: FINISH, FINISH_ONLY_WABA,
      // FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING, FINISH_OBO_MIGRATION,
      // FINISH_GRANT_ONLY_API_ACCESS. Extract the asset IDs when they are
      // provided - never fabricate missing values. The WABA ID and phone
      // number ID are the source of truth for the customer onboarding session.
      console.log('[EmbeddedSignup] SESSION_FINISH_RECEIVED');
      const waba_id = String(
        dataObj.waba_id ||
        (Array.isArray(dataObj.waba_ids) && dataObj.waba_ids.length > 0 ? dataObj.waba_ids[0] : undefined) ||
        ''
      ) || undefined;
      const phone_number_id = String(dataObj.phone_number_id || '') || undefined;
      const business_id = String(dataObj.business_id || '') || undefined;

      if (waba_id) console.log('[EmbeddedSignup] WABA_ID_RECEIVED:', waba_id);
      if (phone_number_id) console.log('[EmbeddedSignup] PHONE_NUMBER_ID_RECEIVED:', phone_number_id);
      if (business_id) console.log('[EmbeddedSignup] BUSINESS_ID_RECEIVED:', business_id);

      // Persist the asset IDs so they can be combined with the exchangeable
      // code once it arrives (whichever arrives last triggers the ONE request).
      if (waba_id || phone_number_id || business_id) {
        signupDataRef.current = { waba_id, phone_number_id, business_id };
        sessionStorage.setItem("meta_embedded_signup", JSON.stringify({
          waba_id,
          phone_number_id,
          business_id,
        }));
      }

      // The exchangeable code is delivered via the FB.login callback. If it has
      // already arrived, complete the connection now; otherwise this call
      // returns and the FB.login callback triggers it once the code lands.
      completeEmbeddedSignup();
    };

    // Register the listener exactly once (cleaned up on unmount so navigating
    // away and back never creates a duplicate listener). Registered on mount -
    // always BEFORE any FB.login() call (Part 1 of the spec).
    window.addEventListener('message', handleEmbeddedSignupMessage);
    console.log('[EmbeddedSignup] Message listener registered');

    // Fetch integration data
    apiGet<IntegrationData>("/api/integrations/me").then((data) => {
      setInteg(data);
      const bType = data.business_type || "product";
      setIntegrationType(bType as "product" | "service");
      setWhatsappForm({
        whatsapp_token: "",
        phone_number_id: data.phone_number_id || "",
        whatsapp_number: data.whatsapp_number || "",
        verify_token: data.verify_token || "",
      });
      setEcommerceForm({
        website_url: bType === "product" ? data.woocommerce_url || "" : data.wp_base_url || "",
        consumer_key: "",
        consumer_secret: "",
      });
    }).catch(console.error);

    // Cleanup: remove the listener so navigating away and back never registers
    // a duplicate listener or processes the same event twice.
    return () => {
      window.removeEventListener('message', handleEmbeddedSignupMessage);
      clearSessionWaitTimeout();
    };
  }, []);

  // Launch WhatsApp Embedded Signup - Official Meta "Embedded Signup
  // Implementation" flow using the JavaScript SDK. FB.login() opens the
  // Embedded Signup in a centered POPUP window and the SaaS page stays open
  // behind it. Meta's SDK delivers:
  //   - the exchangeable code via response.authResponse.code
  //   - the customer's asset IDs (waba_id / phone_number_id / business_id)
  //     via the WA_EMBEDDED_SIGNUP session message posted to THIS window.
  //
  // NOTE on redirect_uri: the code is bound to the canonical production
  // redirect_uri (https://apps.orvym.com/dashboard/integrations/). The
  // callback payload and the backend code exchange use this EXACT value - it
  // is never omitted, never an empty string, never null, never a dynamically
  // computed URI.
  const launchWhatsAppSignup = () => {
    if (!metaConfig) {
      showToast("Meta Embedded Signup is not configured", "error");
      return;
    }

    if (typeof window === 'undefined') return;

    // Synchronously block a second launch while one flow is already running
    // (e.g. a double-click before the disabled re-render). One click produces
    // exactly one dialog launch.
    if (launchingRef.current) {
      console.warn('[EmbeddedSignup] Embedded Signup already in progress - ignoring duplicate launch');
      return;
    }

    if (!facebookSdkReady || !(window as any).FB?.login) {
      showToast("Facebook SDK is still loading. Please try again in a moment.", "error");
      return;
    }

    launchingRef.current = true;
    setConnectingWhatsApp(true);

    // Start a fresh session: reset the one-time exchange lock and drop any
    // WABA/phone/business IDs persisted by a PREVIOUS Embedded Signup run so a
    // stale asset ID can never be attached to a new single-use code. The lock
    // is ONLY reset here - never inside the callback machinery - so a
    // short-lived code is never exchanged more than once.
    completingRef.current = false;
    setIsExchangeInProgress(false);
    clearSessionWaitTimeout();
    sessionStorage.removeItem("meta_embedded_signup");
    signupDataRef.current = {};
    signupCodeRef.current = null;
    messageDiagnosticsRef.current = [];

    // Diagnostics: log the launch context only (never the code).
    console.log('[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)');
    console.log('  Config ID:', metaConfig.config_id);
    console.log('  response_type: code | override_default_response_type: true | extras: {"setup":{},"sessionInfoVersion":3}');

    // Official Meta launch parameters - preserved exactly (Part 13 of the
    // production spec): config_id, response_type: 'code',
    // override_default_response_type: true, extras: { setup: {},
    // sessionInfoVersion: 3 }. sessionInfoVersion is REQUIRED - it instructs
    // Meta to deliver the WA_EMBEDDED_SIGNUP session message carrying the
    // customer asset IDs back to this window. Without it Meta can complete the
    // flow and return the code but never post the session message, which is
    // exactly the failure seen in production.
    (window as any).FB.login((response: any) => {
      try {
        if (response?.authResponse?.code) {
          const code = response.authResponse.code;
          console.log('[EmbeddedSignup] LOGIN_CODE_RECEIVED (length:', code.length, ')');
          // Store the single-use code; it is consumed exactly once by
          // completeEmbeddedSignup (the one-time guard never sends it twice,
          // whether or not the WA_EMBEDDED_SIGNUP asset IDs have arrived yet).
          signupCodeRef.current = code;
          completeEmbeddedSignup();
        } else {
          // User cancelled / denied, or the popup was blocked / errored.
          const status = response?.status || 'unknown';
          const fbError = response?.error;
          if (status === 'connected') {
            // Meta already authorized the user and the actual exchangeable code
            // is delivered through the window.message fallback (the non-JSON
            // redirect message from www.facebook.com), not necessarily through
            // this response. The code may arrive here or there - DO NOT stop
            // the flow: keep waiting for the window message events and let
            // completeEmbeddedSignup fire exactly once when both the code and
            // the WA_EMBEDDED_SIGNUP asset IDs are present.
            console.log('[EmbeddedSignup] FB.login returned without a code. status: connected - continuing to wait for the window message code/session events');
            return;
          }
          console.log('[EmbeddedSignup] FB.login returned without a code. status:', status, fbError || '');
          clearSessionWaitTimeout();
          launchingRef.current = false;
          setIsExchangeInProgress(false);
          setConnectingWhatsApp(false);
          if (fbError) {
            showToast("WhatsApp setup failed: " + (fbError.message || "An error occurred during WhatsApp setup"), "error");
          } else {
            showToast("WhatsApp signup was cancelled. No changes were made.", "info");
          }
        }
      } catch (err: any) {
        console.error('[EmbeddedSignup] FB.login callback error:', err);
        clearSessionWaitTimeout();
        launchingRef.current = false;
        setIsExchangeInProgress(false);
        setConnectingWhatsApp(false);
        showToast("Error launching WhatsApp signup: " + err.message, "error");
      }
    }, {
      config_id: metaConfig.config_id,
      response_type: 'code',
      override_default_response_type: true,
      extras: {
        setup: {},
        sessionInfoVersion: 3,
      },
    });
  };

  // Handle Embedded Signup completion - send the exchangeable code, the
  // canonical redirect_uri and the asset IDs captured from the official
  // WA_EMBEDDED_SIGNUP message to the backend. The backend uses the supplied
  // IDs directly to validate the WABA and phone number; the IDs MUST come from
  // the Embedded Signup session event (the source of truth) - the backend never
  // discovers or guesses them, so this is only called when they are present.
  //
  // redirect_uri is the canonical production constant
  // (https://apps.orvym.com/dashboard/integrations/). It is NEVER omitted,
  // never empty and never null: Meta's code exchange fails with error_subcode
  // 36008 if redirect_uri is missing or differs from the value used in the
  // OAuth dialog request.
  const handleMetaOAuthCallback = async (
    code: string,
    metaData?: { waba_id?: string; phone_number_id?: string; business_id?: string }
  ) => {
    try {
      const wabaId = metaData?.waba_id;
      const phoneNumberId = metaData?.phone_number_id;
      const businessId = metaData?.business_id;

      console.log('[EmbeddedSignup] BACKEND_EXCHANGE_STARTED');
      console.log('  Code length:', code.length);
      console.log('  Frontend redirect_uri:', CANONICAL_REDIRECT_URI);
      console.log('  waba_id:', wabaId || 'not provided');
      console.log('  phone_number_id:', phoneNumberId || 'not provided');
      console.log('  business_id:', businessId || 'not provided');
      console.log('  Note: exchangeable code expires in 30 seconds and is single-use');

      const result = await apiPost("/api/integrations/meta/oauth/callback", {
        code,
        redirect_uri: CANONICAL_REDIRECT_URI,
        waba_id: wabaId || null,
        phone_number_id: phoneNumberId || null,
        business_id: businessId || null,
      });

      if (result.success) {
        console.log('[EmbeddedSignup] BACKEND_EXCHANGE_SUCCESS');
      } else {
        console.log('[EmbeddedSignup] backend request failed:', result.message || 'unknown error');
      }

      if (result.success) {
        sessionStorage.removeItem("meta_embedded_signup");
        showToast("WhatsApp connected successfully!", "success");
        // Refresh integration data
        const updatedInteg = await apiGet<IntegrationData>("/api/integrations/me");
        setInteg(updatedInteg);
        setWhatsappForm({
          whatsapp_token: "",
          phone_number_id: updatedInteg.phone_number_id || "",
          whatsapp_number: updatedInteg.whatsapp_number || "",
          verify_token: updatedInteg.verify_token || "",
        });
        console.log('[EmbeddedSignup] EMBEDDED_SIGNUP_COMPLETE');
      } else {
        showToast(result.message || "Failed to connect WhatsApp", "error");
      }
    } catch (err: any) {
      console.error('[EmbeddedSignup] OAuth callback error:', err);
      showToast("Error: " + err.message, "error");
    } finally {
      // NOTE: the one-time exchange lock (completingRef) is deliberately NOT
      // reset here - it stays held until launchWhatsAppSignup starts a
      // completely new Embedded Signup session, guaranteeing the same
      // single-use code can never be exchanged a second time.
      launchingRef.current = false;
      setIsExchangeInProgress(false);
      setConnectingWhatsApp(false);
    }
  };

  // Disconnect WhatsApp
  const handleDisconnectWhatsApp = async () => {
    if (!confirm("Are you sure you want to disconnect WhatsApp? Your bots, flows, and settings will remain intact.")) {
      return;
    }

    setDisconnectingWhatsApp(true);
    try {
      const result = await apiPost("/api/integrations/whatsapp/disconnect", {});

      if (result.success) {
        showToast("WhatsApp disconnected successfully", "success");
        // Refresh integration data
        const updatedInteg = await apiGet<IntegrationData>("/api/integrations/me");
        setInteg(updatedInteg);
        setWhatsappForm({
          whatsapp_token: "",
          phone_number_id: "",
          whatsapp_number: "",
          verify_token: updatedInteg.verify_token || "",
        });
      } else {
        showToast(result.message || "Failed to disconnect WhatsApp", "error");
      }
    } catch (err: any) {
      showToast("Error: " + err.message, "error");
    } finally {
      setDisconnectingWhatsApp(false);
    }
  };

  // Sync form when integration type changes
  useEffect(() => {
    if (integ) {
      setEcommerceForm({
        website_url: integrationType === "product" ? integ.woocommerce_url || "" : integ.wp_base_url || "",
        consumer_key: "",
        consumer_secret: "",
      });
    }
  }, [integrationType, integ]);

  const handleSaveWhatsApp = async () => {
    if (!whatsappForm.verify_token || !whatsappForm.phone_number_id || !whatsappForm.whatsapp_token || !whatsappForm.whatsapp_number) {
      showToast("All WhatsApp fields are required", "warning");
      return;
    }
    setSavingWhatsApp(true);
    try {
      await apiPatch("/api/integrations/me", {
        whatsapp_token: whatsappForm.whatsapp_token || undefined,
        phone_number_id: whatsappForm.phone_number_id,
        whatsapp_number: whatsappForm.whatsapp_number,
        verify_token: whatsappForm.verify_token.trim(),
      });
      showToast("WhatsApp settings synced", "success");
      apiGet<IntegrationData>("/api/integrations/me").then(setInteg).catch(console.error);
    } catch (err: any) {
      showToast("Error: " + err.message, "error");
    } finally {
      setSavingWhatsApp(false);
    }
  };

  const handleConfigureBase = async () => {
    if (!ecommerceForm.website_url) {
      showToast("Website URL is required", "warning");
      return;
    }

    // Validate URL format
    try {
      new URL(ecommerceForm.website_url);
    } catch {
      showToast("Please enter a valid URL (e.g., https://example.com)", "error");
      return;
    }

    // For product type, validate credentials if provided
    if (integrationType === "product" && (ecommerceForm.consumer_key || ecommerceForm.consumer_secret)) {
      if (!ecommerceForm.consumer_key || !ecommerceForm.consumer_secret) {
        showToast("Both Consumer Key and Consumer Secret are required for WooCommerce", "warning");
        return;
      }
    }

    setSavingEcommerce(true);
    try {
      // Save using the PATCH endpoint for better control
      await apiPatch("/api/integrations/me", {
        business_type: integrationType,
        woocommerce_url: integrationType === "product" ? ecommerceForm.website_url : undefined,
        wp_base_url: integrationType === "service" ? ecommerceForm.website_url : undefined,
        woo_consumer_key: ecommerceForm.consumer_key || undefined,
        woo_consumer_secret: ecommerceForm.consumer_secret || undefined,
      });

      showToast("Platform settings saved successfully!", "success");

      // Refresh integration data
      const updatedInteg = await apiGet<IntegrationData>("/api/integrations/me");
      setInteg(updatedInteg);

      // Update form with saved values
      setEcommerceForm({
        website_url: integrationType === "product" ? updatedInteg.woocommerce_url || "" : updatedInteg.wp_base_url || "",
        consumer_key: "",
        consumer_secret: "",
      });
    } catch (err: any) {
      showToast("Error saving settings: " + err.message, "error");
    } finally {
      setSavingEcommerce(false);
    }
  };

  const handleFetchWebsiteInfo = async () => {
    // Check if URL exists in form
    const formUrl = ecommerceForm.website_url.trim();
    const savedUrl = integrationType === "product" ? integ?.woocommerce_url : integ?.wp_base_url;

    if (!formUrl) {
      showToast("Please enter a website URL first", "warning");
      return;
    }

    // Validate URL format
    try {
      new URL(formUrl);
    } catch {
      showToast("Please enter a valid URL (e.g., https://example.com)", "error");
      return;
    }

    // If URL in form is different from saved URL, save it first
    if (formUrl !== savedUrl) {
      showToast("Saving new URL before fetching...", "info");
      try {
        await apiPatch("/api/integrations/me", {
          business_type: integrationType,
          woocommerce_url: integrationType === "product" ? formUrl : undefined,
          wp_base_url: integrationType === "service" ? formUrl : undefined,
        });

        // Refresh integration data
        const updatedInteg = await apiGet<IntegrationData>("/api/integrations/me");
        setInteg(updatedInteg);
      } catch (err: any) {
        showToast("Error saving URL: " + err.message, "error");
        return;
      }
    }

    // Fetch website info with extended timeout
    setFetchingProducts(true);
    try {
      // Use custom fetch with 90-second timeout for this operation
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 seconds

      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://orym-saas-application.onrender.com';

      const response = await fetch(`${apiUrl}/api/integrations/me/fetch-website-content`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({}),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || errorData?.message || `HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        showToast(result.message || "Website info fetched and cached successfully!", "success");
        // Refresh integration data
        apiGet<IntegrationData>("/api/integrations/me").then(setInteg).catch(console.error);
      } else {
        showToast(result.message || "Failed to fetch website info", "error");
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        showToast("Request timed out. Your website may be too large or slow to respond. Please try again.", "error");
      } else {
        showToast("Error fetching website info: " + err.message, "error");
      }
    } finally {
      setFetchingProducts(false);
    }
  };

  const handleGenerateButton = () => {
    const cleanPhone = phoneNumber.replace(/\D/g, '');
    if (!cleanPhone) {
      showToast("Number required", "warning");
      return;
    }
    const fullNumber = selectedCountry + cleanPhone;
    setButtonCode(`<!-- ORVYM WhatsApp Chat Widget -->\n<a href="https://wa.me/${fullNumber}" target="_blank" style="position:fixed;bottom:20px;right:20px;background:#25D366;color:white;padding:15px 20px;border-radius:50px;text-decoration:none;font-weight:bold;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:9999;">💬 Chat with us</a>`);
    showToast("Code generated", "success");
  };

  if (!integ) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className={`w-16 h-16 border-4 rounded-full animate-spin mx-auto mb-4 ${isDark ? "border-zinc-800" : "border-slate-100"}`} style={{ borderTopColor: isDark ? 'white' : 'black' }}></div>
          <p className={`${isDark ? "text-zinc-600" : "text-slate-500"} font-black uppercase tracking-[0.2em] text-[10px]`}>Linking Nexus...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 max-w-6xl mx-auto pb-24 animate-in fade-in duration-500">
      <ToastContainer />

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className={`text-4xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Integrations</h1>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-2 font-medium`}>Link your WhatsApp Business account and e-commerce platform.</p>
        </div>
        <div className={`flex items-center gap-3 px-6 py-2.5 rounded-[1.5rem] border ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-sm"}`}>
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
          <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-400" : "text-slate-600"}`}>System Active</span>
        </div>
      </div>

      <div className={`flex gap-2 p-2 rounded-[2rem] w-fit border ${isDark ? "bg-[#050505] border-zinc-800" : "bg-slate-100/50"}`}>
        {[
          { id: "whatsapp", label: "WhatsApp" },
          { id: "website", label: "Platform" },
          { id: "button", label: "Chat Widget" }
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id as any)}
            className={`btn-pill ${activeTab === tab.id ? 'btn-pill-active shadow-xl' : 'btn-pill-inactive border-transparent'} px-8`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className={`rounded-[3rem] border overflow-hidden shadow-2xl ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-xl shadow-slate-200/50"}`}>
        {activeTab === "whatsapp" && (
          <div className="p-12 space-y-8">
            <div>
              <h2 className={`text-2xl font-black tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>WhatsApp Business</h2>
              <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-1 font-medium`}>
                {integ.has_whatsapp_token ? "Manage your WhatsApp Business connection" : "Connect your WhatsApp Business Account with Meta"}
              </p>
            </div>

            {integ.has_whatsapp_token && integ.phone_number_id && integ.whatsapp_number ? (
              // Connected State
              <div className={`p-8 rounded-[2rem] border ${isDark ? "bg-black border-zinc-800" : "bg-slate-50/50 border-slate-100"}`}>
                <div className="space-y-6">
                  {/* Status */}
                  <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-2xl bg-green-500/10 flex items-center justify-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      </div>
                      <div>
                        <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Status</p>
                        <p className={`text-sm font-bold ${isDark ? "text-green-400" : "text-green-600"}`}>Connected</p>
                      </div>
                    </div>
                  </div>

                  {/* Phone Number */}
                  <div>
                    <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} mb-2`}>Phone</p>
                    <p className={`text-lg font-mono ${isDark ? "text-white" : "text-slate-900"}`}>{integ.whatsapp_number}</p>
                  </div>

                  {/* Phone Number ID */}
                  <div>
                    <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} mb-2`}>Phone Number ID</p>
                    <p className={`text-sm font-mono ${isDark ? "text-zinc-400" : "text-slate-600"}`}>{integ.phone_number_id}</p>
                  </div>

                  {/* Webhook URL */}
                  <div className={`p-6 rounded-xl border ${isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-slate-200"}`}>
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                      <div>
                        <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Webhook URL</p>
                        <p className={`text-xs font-mono mt-2 ${isDark ? "text-white" : "text-slate-600"} break-all`}>{apiUrl}/webhook</p>
                      </div>
                      <button
                        onClick={() => {navigator.clipboard.writeText(`${apiUrl}/webhook`); showToast("Copied","success")}}
                        className="btn-secondary !py-2 whitespace-nowrap"
                      >
                        Copy URL
                      </button>
                    </div>
                  </div>

                  {/* Verify Token */}
                  <div className={`p-6 rounded-xl border ${isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-slate-200"}`}>
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                      <div>
                        <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Verify Token</p>
                        <p className={`text-xs font-mono mt-2 ${isDark ? "text-white" : "text-slate-600"}`}>{integ.verify_token}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {navigator.clipboard.writeText(integ.verify_token); showToast("Copied","success")}}
                          className="btn-secondary !py-2 whitespace-nowrap"
                        >
                          Copy
                        </button>
                        <button onClick={handleGenerateAndSave} className="btn-secondary !py-2 whitespace-nowrap">
                          Regenerate
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-4 pt-4">
                    {metaConfig && (
                      <button
                            onClick={launchWhatsAppSignup}
                        disabled={connectingWhatsApp || isExchangeInProgress}
                        className="btn-secondary flex-1"
                      >
                        {connectingWhatsApp || isExchangeInProgress ? <div className="w-4 h-4 border-2 border-slate-600/30 border-t-slate-600 rounded-full animate-spin" /> : "Reconnect"}
                      </button>
                    )}
                    <button
                      onClick={handleDisconnectWhatsApp}
                      disabled={disconnectingWhatsApp}
                      className="btn-secondary flex-1 !bg-red-500/10 !text-red-500 !border-red-500/20 hover:!bg-red-500/20"
                    >
                      {disconnectingWhatsApp ? <div className="w-4 h-4 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" /> : "Disconnect"}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // Not Connected State - Professional Meta Embedded Signup
              <div className="space-y-6">
                {metaConfig ? (
                  // Professional Embedded Signup Card
                  <div className={`rounded-3xl border overflow-hidden ${isDark ? "bg-gradient-to-br from-zinc-900 to-black border-zinc-800" : "bg-gradient-to-br from-white to-slate-50 border-slate-200"}`}>
                    <div className="p-12">
                      <div className="max-w-xl mx-auto">
                        {/* Header Section */}
                        <div className="text-center space-y-4 mb-8">
                          {/* Professional Icon */}
                          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-500/20">
                            <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                          </div>

                          {/* Title and Description */}
                          <div>
                            <h3 className={`text-2xl font-bold tracking-tight mb-2 ${isDark ? "text-white" : "text-slate-900"}`}>
                              WhatsApp Business Integration
                            </h3>
                            <p className={`text-base ${isDark ? "text-zinc-400" : "text-slate-600"} max-w-md mx-auto leading-relaxed`}>
                              Connect your WhatsApp Business Account securely through Meta's official integration platform
                            </p>
                          </div>
                        </div>

                        {/* Features List */}
                        <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 p-6 rounded-2xl ${isDark ? "bg-zinc-900/50 border border-zinc-800" : "bg-slate-100/50 border border-slate-200"}`}>
                          <div className="flex items-start gap-3">
                            <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 ${isDark ? "bg-green-500/20" : "bg-green-100"}`}>
                              <svg className={`w-3 h-3 ${isDark ? "text-green-400" : "text-green-600"}`} fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div>
                              <p className={`text-sm font-semibold ${isDark ? "text-zinc-200" : "text-slate-900"}`}>Secure OAuth</p>
                              <p className={`text-xs ${isDark ? "text-zinc-500" : "text-slate-500"}`}>End-to-end encrypted</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 ${isDark ? "bg-green-500/20" : "bg-green-100"}`}>
                              <svg className={`w-3 h-3 ${isDark ? "text-green-400" : "text-green-600"}`} fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div>
                              <p className={`text-sm font-semibold ${isDark ? "text-zinc-200" : "text-slate-900"}`}>One-Click Setup</p>
                              <p className={`text-xs ${isDark ? "text-zinc-500" : "text-slate-500"}`}>No manual configuration</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 ${isDark ? "bg-green-500/20" : "bg-green-100"}`}>
                              <svg className={`w-3 h-3 ${isDark ? "text-green-400" : "text-green-600"}`} fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div>
                              <p className={`text-sm font-semibold ${isDark ? "text-zinc-200" : "text-slate-900"}`}>Instant Sync</p>
                              <p className={`text-xs ${isDark ? "text-zinc-500" : "text-slate-500"}`}>Real-time connection</p>
                            </div>
                          </div>
                        </div>

                        {/* Connect Button */}
                        <div className="space-y-4">
                          <button
                        onClick={launchWhatsAppSignup}
                            disabled={connectingWhatsApp || isExchangeInProgress}
                            className={`w-full py-4 px-6 rounded-xl font-semibold text-base transition-all duration-200 transform ${
                              connectingWhatsApp || isExchangeInProgress
                                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white cursor-not-allowed opacity-70'
                                : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:scale-[1.02] active:scale-[0.98]'
                            }`}
                          >
                            {connectingWhatsApp || isExchangeInProgress ? (
                              <div className="flex items-center justify-center gap-3">
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                <span>Connecting...</span>
                              </div>
                            ) : (
                              <div className="flex items-center justify-center gap-3">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                                </svg>
                                <span>Connect WhatsApp Business</span>
                              </div>
                            )}
                          </button>

                          {/* Footer Note */}
                          <div className={`text-center text-xs ${isDark ? "text-zinc-500" : "text-slate-500"}`}>
                            <p>Powered by Meta • You'll be redirected to complete the secure authorization process</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Configuration Required State
                  <div className={`rounded-3xl border p-12 ${isDark ? "bg-zinc-900 border-zinc-800" : "bg-slate-50 border-slate-200"}`}>
                    <div className="max-w-md mx-auto text-center space-y-6">
                      {/* Warning Icon */}
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10 border-2 border-amber-500/20">
                        <svg className="w-8 h-8 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                      </div>

                      {/* Message */}
                      <div>
                        <h3 className={`text-lg font-bold mb-2 ${isDark ? "text-amber-400" : "text-amber-700"}`}>
                          Configuration Required
                        </h3>
                        <p className={`text-sm ${isDark ? "text-zinc-400" : "text-slate-600"} leading-relaxed`}>
                          Meta Embedded Signup is not configured on the server. Please contact your system administrator or configure the required Meta credentials in the backend environment.
                        </p>
                      </div>

                      {/* Action Button */}
                      <div className={`p-4 rounded-xl ${isDark ? "bg-zinc-800/50" : "bg-slate-100"}`}>
                        <p className={`text-xs font-medium ${isDark ? "text-zinc-500" : "text-slate-500"}`}>
                          Required: META_APP_ID, META_CONFIG_ID, META_APP_SECRET
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === "website" && (
          <div className="p-12 space-y-10">
            <div>
              <h2 className={`text-2xl font-black tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Platform Integration</h2>
              <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-1 font-medium`}>Synchronize your Nexus with your store's inventory and data.</p>
            </div>

            <div className="space-y-8">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Base URL</label>
                  {(integrationType === "product" ? integ?.woocommerce_url : integ?.wp_base_url) && (
                    <span className={`text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
                      <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                      Saved
                    </span>
                  )}
                </div>
                <input type="text" value={ecommerceForm.website_url} onChange={e => setEcommerceForm({...ecommerceForm, website_url: e.target.value})}
                  className="input-field" placeholder="https://your-store-address.com" />
              </div>

              <div className="space-y-4">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Integration Type</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[
                    { id: "product", icon: "🛍️", label: "Inventory Mode", sub: "WooCommerce Products" },
                    { id: "service", icon: "🏗️", label: "Service Mode", sub: "Static Website Content" }
                  ].map(type => (
                    <button key={type.id} onClick={() => setIntegrationType(type.id as any)}
                      className={`p-6 rounded-[2rem] border-2 transition-all duration-300 flex items-center gap-5 ${
                        integrationType === type.id
                          ? isDark ? "border-white bg-zinc-900 shadow-2xl" : "border-slate-500 bg-slate-50/50 shadow-xl"
                          : isDark ? "border-zinc-800 hover:border-zinc-700 bg-black" : "border-slate-100 hover:border-slate-200 bg-white"
                      }`}
                    >
                      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl shadow-inner ${isDark ? "bg-zinc-800" : "bg-white border border-slate-100"}`}>{type.icon}</div>
                      <div className="text-left">
                        <p className={`font-black text-sm uppercase tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>{type.label}</p>
                        <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>{type.sub}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {integrationType === "product" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
                  <div className="space-y-3">
                    <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Consumer Key</label>
                    <input type="text" value={ecommerceForm.consumer_key} onChange={e => setEcommerceForm({...ecommerceForm, consumer_key: e.target.value})}
                      className="input-field" placeholder="ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                  </div>
                  <div className="space-y-3">
                    <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Consumer Secret</label>
                    <input type="password" value={ecommerceForm.consumer_secret} onChange={e => setEcommerceForm({...ecommerceForm, consumer_secret: e.target.value})}
                      className="input-field" placeholder="cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-4 pt-6">
              <button
                onClick={handleFetchWebsiteInfo}
                disabled={fetchingProducts || !ecommerceForm.website_url.trim()}
                className="btn-secondary min-w-[240px] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {fetchingProducts ? <div className="w-4 h-4 border-2 border-slate-600/30 border-t-slate-600 rounded-full animate-spin" /> : "Fetch Website Info"}
              </button>
              <button onClick={handleConfigureBase} disabled={savingEcommerce} className="btn-primary min-w-[240px]">
                {savingEcommerce ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Save Platform Settings"}
              </button>
            </div>

            <div className={`p-4 rounded-2xl border ${isDark ? "bg-blue-950/20 border-blue-900/30 text-blue-400" : "bg-blue-50 border-blue-200 text-blue-700"}`}>
              <p className="text-xs font-medium">💡 Enter your website URL and click "Fetch Website Info" to automatically cache your site content for AI responses. The URL will be saved automatically.</p>
            </div>
          </div>
        )}

        {activeTab === "button" && (
          <div className="p-12 space-y-10">
            <div className="text-center max-w-xl mx-auto">
              <h2 className={`text-2xl font-black tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Floating Chat Widget</h2>
              <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-1 font-medium`}>Create a bridge between your website and your professional WhatsApp bot.</p>
            </div>

            <div className="max-w-md mx-auto space-y-8">
              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Select Country</label>
                <select value={selectedCountry} onChange={e => setSelectedCountry(e.target.value)}
                  className="select-field">
                  {countries.map(country => (
                    <option key={country.code} value={country.code}>
                      {country.flag} {country.name} ({country.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Phone Number (without country code)</label>
                <input type="text" value={phoneNumber} onChange={e => setPhoneNumber(e.target.value)}
                  className="input-field text-center" placeholder="300 1234567" />
              </div>

              <button onClick={handleGenerateButton} className="btn-primary w-full py-4 text-xs tracking-[0.2em]">
                Generate Widget Code
              </button>

              {buttonCode && (
                <div className={`p-8 rounded-[2rem] border font-mono text-xs shadow-inner ${isDark ? "bg-black border-zinc-800 text-slate-400" : "bg-slate-50 border-slate-200 text-slate-600"}`}>
                  <pre className="whitespace-pre-wrap leading-relaxed">{buttonCode}</pre>
                  <button onClick={() => {navigator.clipboard.writeText(buttonCode); showToast("Copied", "success")}} className="mt-6 btn-secondary w-full !py-2.5">
                    Copy Integration Code
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
