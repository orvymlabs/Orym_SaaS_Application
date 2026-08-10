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

  // Official Meta Embedded Signup flow (JS SDK): FB.login() opens the Embedded
  // Signup in a centered popup window and the SaaS page stays open behind it.
  // On completion Meta:
  //   1. posts a WA_EMBEDDED_SIGNUP session message to THIS window (the window
  //      that spawned the flow) carrying the customer's asset IDs
  //      (waba_id, phone_number_id, business_id) - captured below.
  //   2. delivers the exchangeable code to the FB.login callback
  //      (response.authResponse.code).
  // The code + asset IDs are sent to the backend, which uses the supplied IDs
  // directly (no /me/businesses discovery is needed when they are present).
  const signupCodeRef = useRef<string | null>(null);
  const signupDataRef = useRef<{ waba_id?: string; phone_number_id?: string; business_id?: string }>({});
  const completingRef = useRef(false);
  // Synchronous guard against duplicate launches (e.g. a fast double-click
  // before React re-renders the disabled state). It is cleared again when the
  // flow finishes, cancels or errors, so reconnect/retry keeps working.
  const launchingRef = useRef(false);
  // Guards against scheduling more than one retry chain - the exchangeable
  // code arrives via the FB.login callback while the asset IDs arrive via the
  // WA_EMBEDDED_SIGNUP message a moment later.
  const retryScheduledRef = useRef(false);

  // Complete the connection exactly once, as soon as the single-use
  // exchangeable code is available. The code is cleared as soon as the backend
  // callback is started so it can never be exchanged twice. Because the code
  // (FB.login callback) and the asset IDs (WA_EMBEDDED_SIGNUP message) can
  // arrive in either order, retry briefly (up to ~6s) to collect the asset IDs
  // from the completion event before calling the backend - they are the
  // source of truth for the WABA / phone number, so /me/businesses discovery
  // on the backend is never needed in this flow.
  const completeEmbeddedSignup = (retriesLeft = 12) => {
    if (completingRef.current) return true;
    const code = signupCodeRef.current;
    const ids = signupDataRef.current;
    // Send as soon as the code is available AND either the asset IDs arrived
    // from the WA_EMBEDDED_SIGNUP event or we have waited long enough for them.
    if (code && (ids.waba_id || ids.phone_number_id || retriesLeft <= 5)) {
      completingRef.current = true;
      retryScheduledRef.current = false;
      signupCodeRef.current = null;
      handleMetaOAuthCallback(code, { ...ids });
      return true;
    }
    if (retriesLeft <= 0) {
      retryScheduledRef.current = false;
      launchingRef.current = false;
      setConnectingWhatsApp(false);
      showToast(
        "WhatsApp Embedded Signup finished but no exchangeable code was returned. Please try again.",
        "error"
      );
      return false;
    }
    if (!retryScheduledRef.current) {
      retryScheduledRef.current = true;
      setTimeout(() => {
        retryScheduledRef.current = false;
        completeEmbeddedSignup(retriesLeft - 1);
      }, 500);
    }
    return false;
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
    const handleEmbeddedSignupMessage = (event: MessageEvent) => {
      // Security check: only accept messages from facebook.com
      if (!event.origin.endsWith('facebook.com')) return;

      let data: any;
      try {
        data = JSON.parse(event.data);
      } catch {
        return; // non-JSON message from facebook.com - ignore
      }

      if (!data || data.type !== 'WA_EMBEDDED_SIGNUP') return;

      const eventName = String(data.event || 'UNKNOWN');
      const dataObj = data.data || {};

      console.log('[EmbeddedSignup] message event received from', event.origin, '| event:', eventName);

      // CANCEL - abandoned flow (capture current_step) or user-reported error
      // (capture error_message, error_code, session_id, timestamp).
      if (eventName === 'CANCEL') {
        const errorMessage = dataObj.error_message;
        const errorCode = dataObj.error_code;
        if (errorMessage || errorCode) {
          console.log('[EmbeddedSignup] Flow error reported:', {
            error_message: errorMessage,
            error_code: errorCode,
            session_id: dataObj.session_id,
            timestamp: dataObj.timestamp,
          });
          launchingRef.current = false;
          setConnectingWhatsApp(false);
          showToast(
            "WhatsApp setup failed: " + (errorMessage || "An error occurred during WhatsApp setup"),
            "error"
          );
        } else {
          console.log('[EmbeddedSignup] Flow cancelled. current_step:', dataObj.current_step || 'unknown');
          launchingRef.current = false;
          setConnectingWhatsApp(false);
          showToast("WhatsApp signup was cancelled. No changes were made.", "info");
        }
        return;
      }

      // ERROR - customer encountered an error during onboarding.
      if (eventName === 'ERROR') {
        const errorMessage = dataObj.error_message;
        const errorCode = dataObj.error_code;
        console.log('[EmbeddedSignup] Flow error:', errorCode, errorMessage);
        launchingRef.current = false;
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
      // provided - never fabricate missing values (the backend resolves any
      // missing ones server-side after the token exchange).
      const waba_id = dataObj.waba_id ||
        (Array.isArray(dataObj.waba_ids) && dataObj.waba_ids.length > 0 ? String(dataObj.waba_ids[0]) : undefined);
      const phone_number_id = dataObj.phone_number_id || undefined;
      const business_id = dataObj.business_id || undefined;

      console.log('[EmbeddedSignup] waba_id captured:', waba_id || 'not provided');
      console.log('[EmbeddedSignup] phone_number_id captured:', phone_number_id || 'not provided');
      console.log('[EmbeddedSignup] business_id captured:', business_id || 'not provided');

      // Persist the asset IDs (covers the popup-closed-early case) so they can
      // be combined with the exchangeable code once it arrives.
      if (waba_id || phone_number_id || business_id) {
        signupDataRef.current = { waba_id, phone_number_id, business_id };
        sessionStorage.setItem("meta_embedded_signup", JSON.stringify({
          waba_id,
          phone_number_id,
          business_id,
        }));
      }

      // The exchangeable code is delivered via the FB.login callback. If it has
      // already arrived, complete the connection now; otherwise retry briefly.
      completeEmbeddedSignup();
    };

    // Register the listener exactly once (cleaned up on unmount so navigating
    // away and back never creates a duplicate listener).
    window.addEventListener('message', handleEmbeddedSignupMessage);

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
  // NOTE on redirect_uri: with the FB.login popup the code is returned directly
  // to the JS callback - there is NO redirect, so Meta does not record a
  // redirect_uri for the code. Sending any redirect_uri in the server-side
  // exchange fails with error_subcode 36008 ("redirect_uri identical"). The
  // backend therefore omits redirect_uri entirely for this flow (it is sent as
  // null in the callback payload).
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

    // Start a fresh session: drop any WABA/phone/business IDs persisted by a
    // PREVIOUS Embedded Signup run so a stale asset ID can never be attached to
    // a new single-use code.
    sessionStorage.removeItem("meta_embedded_signup");
    signupDataRef.current = {};
    signupCodeRef.current = null;

    // Diagnostics: log the launch context only (never the code).
    console.log('[EmbeddedSignup] Launching WhatsApp Embedded Signup via FB.login popup (official Meta flow)');
    console.log('  Config ID:', metaConfig.config_id);
    console.log('  response_type: code | override_default_response_type: true | extras: {"setup":{}}');

    // Official Meta launch parameters - preserved exactly:
    // config_id, response_type: 'code', override_default_response_type: true,
    // extras: { setup: {} }.
    (window as any).FB.login((response: any) => {
      try {
        if (response?.authResponse?.code) {
          const code = response.authResponse.code;
          console.log('[EmbeddedSignup] exchangeable code received via FB.login callback (length:', code.length, ')');
          // Store the single-use code; it is consumed exactly once by
          // completeEmbeddedSignup (which waits for the WA_EMBEDDED_SIGNUP
          // asset IDs before calling the backend).
          signupCodeRef.current = code;
          completeEmbeddedSignup();
        } else {
          // User cancelled / denied, or the popup was blocked / errored.
          const status = response?.status || 'unknown';
          const fbError = response?.error;
          console.log('[EmbeddedSignup] FB.login returned without a code. status:', status, fbError || '');
          launchingRef.current = false;
          setConnectingWhatsApp(false);
          if (fbError) {
            showToast("WhatsApp setup failed: " + (fbError.message || "An error occurred during WhatsApp setup"), "error");
          } else {
            showToast("WhatsApp signup was cancelled. No changes were made.", "info");
          }
        }
      } catch (err: any) {
        console.error('[EmbeddedSignup] FB.login callback error:', err);
        launchingRef.current = false;
        setConnectingWhatsApp(false);
        showToast("Error launching WhatsApp signup: " + err.message, "error");
      }
    }, {
      config_id: metaConfig.config_id,
      response_type: 'code',
      override_default_response_type: true,
      extras: { setup: {} },
    });
  };

  // Handle Embedded Signup completion - send the exchangeable code and the
  // asset IDs captured from the official WA_EMBEDDED_SIGNUP message to the
  // backend. The backend uses the supplied IDs directly to validate the WABA
  // and phone number (no server-side /me/businesses discovery is needed).
  //
  // redirect_uri is deliberately sent as null: in the FB.login popup flow the
  // code is returned directly to the JS callback (no redirect), so Meta does
  // not record a redirect_uri for it. Sending one would fail the exchange with
  // error_subcode 36008. The backend omits redirect_uri when it is null.
  const handleMetaOAuthCallback = async (
    code: string,
    metaData?: { waba_id?: string; phone_number_id?: string; business_id?: string }
  ) => {
    try {
      // The WABA / phone / business IDs come from the WA_EMBEDDED_SIGNUP
      // FINISH message event. Fall back to any persisted value (covers a popup
      // that closed before the listener stored them).
      const stored = sessionStorage.getItem("meta_embedded_signup");
      const parsed = stored ? JSON.parse(stored) : {};
      const wabaId = metaData?.waba_id || parsed.waba_id;
      const phoneNumberId = metaData?.phone_number_id || parsed.phone_number_id;
      const businessId = metaData?.business_id || parsed.business_id;

      console.log('[EmbeddedSignup] backend request started');
      console.log('  Code length:', code.length);
      console.log('  waba_id:', wabaId || 'not provided');
      console.log('  phone_number_id:', phoneNumberId || 'not provided');
      console.log('  business_id:', businessId || 'not provided');
      console.log('  Note: FB.login popup code - redirect_uri omitted in exchange (per Meta docs)');
      console.log('  Note: Exchangeable code expires in 30 seconds');

      const result = await apiPost("/api/integrations/meta/oauth/callback", {
        code,
        redirect_uri: null,
        waba_id: wabaId || null,
        phone_number_id: phoneNumberId || null,
        business_id: businessId || null,
      });

      console.log('[EmbeddedSignup] backend request succeeded:', result.success ? 'SUCCESS' : 'FAILED');

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
      } else {
        showToast(result.message || "Failed to connect WhatsApp", "error");
      }
    } catch (err: any) {
      console.error('[EmbeddedSignup] OAuth callback error:', err);
      showToast("Error: " + err.message, "error");
    } finally {
      completingRef.current = false;
      launchingRef.current = false;
      setConnectingWhatsApp(false);
    }
  };

  // Redirect-back fallback handler (legacy). The official FB.login popup flow
  // returns the code to the JS callback and does NOT redirect back to this
  // page, so this normally never fires. It only covers a leftover manual-dialog
  // tab from an older deployment: if the page loads with ?code=...&state=...
  // (or ?error=...), the CSRF state is verified against the value stored at
  // launch, the params are stripped from the URL immediately (so a refresh can
  // NEVER re-submit the single-use code), and the code is sent to the backend
  // exactly once.
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const oauthError = params.get('error');

    if (!code && !oauthError) return;

    const expectedState = sessionStorage.getItem("meta_embedded_signup_state");
    sessionStorage.removeItem("meta_embedded_signup_state");
    const cleanUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({}, "", cleanUrl);

    if (expectedState && state && state !== expectedState) {
      // CSRF mismatch - the code does not belong to this launch. Abort.
      console.warn('[EmbeddedSignup] state mismatch on OAuth redirect-back - ignoring code');
      launchingRef.current = false;
      setConnectingWhatsApp(false);
      showToast("WhatsApp signup validation failed. Please try again.", "error");
      return;
    }

    if (oauthError) {
      console.log('[EmbeddedSignup] OAuth dialog returned error:', oauthError);
      launchingRef.current = false;
      setConnectingWhatsApp(false);
      showToast("WhatsApp signup was cancelled. No changes were made.", "info");
      return;
    }

    if (code) {
      console.log('[EmbeddedSignup] exchangeable code received via OAuth redirect-back (length:', code.length, ')');
      // Mark the single exchange as in progress so the message-driven retry
      // machinery can never submit this code a second time.
      completingRef.current = true;
      setConnectingWhatsApp(true);
      handleMetaOAuthCallback(code);
    }
  }, []);

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
                        disabled={connectingWhatsApp}
                        className="btn-secondary flex-1"
                      >
                        {connectingWhatsApp ? <div className="w-4 h-4 border-2 border-slate-600/30 border-t-slate-600 rounded-full animate-spin" /> : "Reconnect"}
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
                            disabled={connectingWhatsApp}
                            className={`w-full py-4 px-6 rounded-xl font-semibold text-base transition-all duration-200 transform ${
                              connectingWhatsApp
                                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white cursor-not-allowed opacity-70'
                                : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:scale-[1.02] active:scale-[0.98]'
                            }`}
                          >
                            {connectingWhatsApp ? (
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
