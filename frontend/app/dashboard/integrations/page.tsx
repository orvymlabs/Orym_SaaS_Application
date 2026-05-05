"use client";
import { useEffect, useState } from "react";
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

  useEffect(() => {
    apiGet<any>("/api/auth/usage").then((data) => {
      if (data?.plan) setUserPlan(data.plan);
    }).catch(console.error);

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
  }, []);

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
      showToast("URL required", "warning");
      return;
    }
    setSavingEcommerce(true);
    try {
      await apiPost("/api/integrations/me/configure-base", {
        integration_type: integrationType,
        website_url: ecommerceForm.website_url,
        consumer_key: ecommerceForm.consumer_key,
        consumer_secret: ecommerceForm.consumer_secret,
      });
      showToast("Website configured", "success");
      apiGet<IntegrationData>("/api/integrations/me").then(setInteg).catch(console.error);
    } catch (err: any) {
      showToast("Error: " + err.message, "error");
    } finally {
      setSavingEcommerce(false);
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
              <h2 className={`text-2xl font-black tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>WhatsApp Integration</h2>
              <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-1 font-medium`}>Configure your WhatsApp Business API credentials.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Phone Number ID <span className="text-red-500">*</span></label>
                <input type="text" value={whatsappForm.phone_number_id} onChange={e => setWhatsappForm({...whatsappForm, phone_number_id: e.target.value})}
                  className="input-field" placeholder="Enter your Phone Number ID (e.g. 109283...)" required />
              </div>
              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Verify Token <span className="text-red-500">*</span></label>
                <div className="flex gap-3">
                  <input type="text" readOnly value={whatsappForm.verify_token} className="input-field !bg-zinc-100/50 dark:!bg-zinc-900/50 !cursor-not-allowed" required />
                  <button onClick={handleGenerateAndSave} className="btn-success whitespace-nowrap">Generate</button>
                </div>
              </div>
            </div>

            <div className={`p-8 rounded-[2rem] border ${isDark ? "bg-black border-zinc-800" : "bg-slate-50/50 border-slate-100"}`}>
              <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div>
                  <p className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Webhook Callback URL</p>
                  <p className={`text-sm font-mono mt-2 ${isDark ? "text-white" : "text-slate-600"} break-all`}>{apiUrl}/webhook</p>
                </div>
                <button onClick={() => {navigator.clipboard.writeText(`${apiUrl}/webhook`); showToast("Copied","success")}} className="btn-secondary !py-2.5">Copy URL</button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Business Number <span className="text-red-500">*</span></label>
                <input type="text" value={whatsappForm.whatsapp_number} onChange={e => setWhatsappForm({...whatsappForm, whatsapp_number: e.target.value})}
                  className="input-field" placeholder="+1 234 567 8900" required />
              </div>
              <div className="space-y-3">
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Access Token <span className="text-red-500">*</span></label>
                <input type="password" value={whatsappForm.whatsapp_token} onChange={e => setWhatsappForm({...whatsappForm, whatsapp_token: e.target.value})}
                  className="input-field" placeholder="Enter your Permanent Access Token..." required />
              </div>
            </div>

            <div className="flex justify-end pt-6">
              <button onClick={handleSaveWhatsApp} disabled={savingWhatsApp} className="btn-primary min-w-[240px]">
                {savingWhatsApp ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Save WhatsApp Settings"}
              </button>
            </div>
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
                <label className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"} ml-1`}>Base URL</label>
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

            <div className="flex justify-end pt-6">
              <button onClick={handleConfigureBase} disabled={savingEcommerce} className="btn-primary min-w-[240px]">
                {savingEcommerce ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Save Platform Settings"}
              </button>
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
