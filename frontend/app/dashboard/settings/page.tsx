"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui";

const PROVIDER_INFO: Record<string, {label: string}> = {
  openrouter: { label: "OpenRouter" },
  openai: { label: "OpenAI" },
  gemini: { label: "Google Gemini" },
  qwen: { label: "Qwen" }
};

const MODELS: Record<string, any[]> = {
  openrouter: [
    {"value": "openai/gpt-4o", "label": "GPT-4o", "desc": "Most intelligent model", "badge": "Premium"},
    {"value": "anthropic/claude-3.5-sonnet", "label": "Claude 3.5 Sonnet", "desc": "Best for coding & nuance", "badge": "Popular"},
    {"value": "google/gemini-pro-1.5", "label": "Gemini Pro 1.5", "desc": "Huge context window", "badge": "New"},
    {"value": "meta-llama/llama-3.1-70b-instruct", "label": "Llama 3.1 70B", "desc": "Top open source model", "badge": "Open"},
    {"value": "openai/gpt-oss-20b:free", "label": "GPT-OSS 20B", "desc": "Good for simple tasks", "badge": "Free"},
  ],
  openai: [
    {"value": "gpt-4o", "label": "GPT-4o", "desc": "Flagship high-intelligence model", "badge": "Latest"},
    {"value": "gpt-4o-mini", "label": "GPT-4o Mini", "desc": "Fast & affordable for most tasks", "badge": "Fast"},
    {"value": "o1", "label": "O1", "desc": "Advanced reasoning & logic", "badge": "Reasoning"},
    {"value": "o1-mini", "label": "O1 Mini", "desc": "Fast reasoning & logic", "badge": "Logic"},
    {"value": "o3-mini", "label": "O3 Mini", "desc": "Latest reasoning model", "badge": "Latest"},
  ],
  gemini: [
    {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash", "desc": "Ultra-fast flagship model", "badge": "Speed"},
    {"value": "gemini-2.0-pro", "label": "Gemini 2.0 Pro", "desc": "Highest intelligence Gemini", "badge": "Pro"},
    {"value": "gemini-2.0-flash-lite", "label": "Gemini 2.0 Lite", "desc": "Efficient everyday model", "badge": "Efficient"},
  ],
  qwen: [
    {"value": "qwen-plus", "label": "Qwen Plus", "desc": "Enhanced capabilities", "badge": "Balanced"},
    {"value": "qwen-max", "label": "Qwen Max", "desc": "Maximum intelligence", "badge": "Powerful"},
    {"value": "qwen-turbo", "label": "Qwen Turbo", "desc": "Extremely fast response", "badge": "Turbo"},
    {"value": "qwen-long", "label": "Qwen Long", "desc": "Long context support", "badge": "Context"},
  ],
};

export default function SettingsPage() {
  const [bot, setBot] = useState<any>(null);
  const [settings, setSettings] = useState<any>(null);
  const [mode, setMode] = useState("default");
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openrouter");
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [temperature, setTemperature] = useState(70);
  const [language, setLanguage] = useState("english"); 
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<Record<string, string>>({});
  const [templateEnabled, setTemplateEnabled] = useState(true);
  const [templateStatuses, setTemplateStatuses] = useState<Record<string, boolean>>({});
  const [customResponses, setCustomResponses] = useState<Array<{keyword: string, response: string}>>([]);
  const [customProducts, setCustomProducts] = useState<Array<{name: string, description: string, image_url: string}>>([]);
  
  const { showToast, ToastContainer } = useToast();

  const templateConfigs = [
    { id: 'greeting', name: 'Greeting Message', placeholder: '👋 Hi {user_name}! Welcome to {site_name}. Type *menu* to see how I can help you today!' },
    { id: 'menu', name: 'Main Menu', placeholder: '📋 *Main Menu*\n\n1. Services\n2. Order Products\n3. Product Catalog\n\n💬 Reply with a number to continue!' },
    { id: 'services', name: 'Services', placeholder: '🏭 *Our Services*\n\nOur services include:\n• Web Development\n• Mobile Apps\n• UI/UX Design' },
    { id: 'order', name: 'Order', placeholder: '🛍️ *Order Products*\n\nBrowse our product catalog and place your order!' },
    { id: 'product_list', name: 'Product Catalog', placeholder: '🛍️ *Product Catalog* ({total} items)\n\n{item_list}\n\n💬 Reply with a product name to order!' },
    { id: 'delivery', name: 'Delivery Info', placeholder: '🚚 *Delivery Information*\n\nWe offer fast nationwide delivery within 3-5 business days.' },
    { id: 'contact', name: 'Contact Us', placeholder: '📞 *Contact Us*\n\n🏢 {site_name}\n📱 {phone}\n📧 {email}\n📍 {address}' },
  ];

  useEffect(() => {
    Promise.all([
      api("/api/bots/me").catch(() => null),
      api("/api/bots/settings").catch(() => null),
    ]).then(([b, s]) => {
      setBot(b);
      if (b) setMode(b.mode);
      if (s) {
        setSettings(s);
        setPrompt(s.prompt || "");
        const currentProvider = s.model_name || "openrouter";
        setProvider(currentProvider);
        const availableModels = MODELS[currentProvider] || MODELS.openrouter;
        setModelName(s.specific_model_name || availableModels[0].value);
        setTemperature(s.temperature || 70);
        setLanguage(s.language || "english");

        // Load templates - handle both old format (greeting) and new format (template_greeting)
        const loadedTemplates: Record<string, string> = {};
        const rawTemplates = s.templates || s.custom_responses || {};
        if (rawTemplates && typeof rawTemplates === 'object') {
          Object.entries(rawTemplates).forEach(([key, value]) => {
            if (typeof value === 'string' && !key.includes('_enabled')) {
              loadedTemplates[key] = value;
            }
          });
        }
        setTemplates(loadedTemplates);

        setTemplateEnabled(s.template_enabled ?? true);

        // Load template statuses with defaults
        const defaultStatuses: Record<string, boolean> = {
          'template_services_enabled': false,
          'template_order_enabled': true,
          'template_product_list_enabled': true,
          'template_delivery_enabled': true,
          'template_contact_enabled': true,
          'template_greeting_enabled': true,
          'template_menu_enabled': true,
        };
        const loadedStatuses = s.template_statuses || {};
        setTemplateStatuses({ ...defaultStatuses, ...loadedStatuses });

        if (s.custom_responses && typeof s.custom_responses === "object") {
          const entries = Object.entries(s.custom_responses).map(([keyword, response]) => ({
            keyword,
            response: response as string,
          }));
          setCustomResponses(entries);
        }
        if (s.custom_products && Array.isArray(s.custom_products)) {
          setCustomProducts(s.custom_products);
        }
      }
    });
  }, []);

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const customResponsesObj: Record<string, string> = {};
      customResponses.forEach(cr => {
        if (cr.keyword.trim()) {
          customResponsesObj[cr.keyword.trim().toLowerCase()] = cr.response;
        }
      });

      await Promise.all([
        api("/api/bots/mode", { method: "PATCH", body: JSON.stringify({ mode }) }),
        api("/api/bots/settings", {
          method: "PATCH",
          body: JSON.stringify({
            prompt,
            model_name: provider,
            specific_model_name: modelName,
            temperature,
            language,
            custom_responses: customResponsesObj,
            custom_products: customProducts.filter(p => p.name.trim()),
            templates,
            template_enabled: templateEnabled,
            template_statuses: templateStatuses,
            ...(apiKey ? { api_key: apiKey } : {}),
          }),
        }),
      ]);

      const updatedSettings = await api("/api/bots/settings");
      setSettings(updatedSettings);
      showToast("Settings saved successfully!", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadJSON = () => {
    const data = {
      mode,
      custom_responses: customResponses,
      templates,
      template_enabled: templateEnabled,
      template_statuses: templateStatuses 
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bot-settings-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUploadJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (json.custom_responses) setCustomResponses(json.custom_responses);
        if (json.templates) setTemplates(json.templates);
        if (typeof json.template_enabled === 'boolean') setTemplateEnabled(json.template_enabled);
        if (json.template_statuses && typeof json.template_statuses === 'object') setTemplateStatuses(json.template_statuses);
        showToast("JSON settings loaded! Don't forget to save.", "success");
      } catch (err) {
        showToast("Invalid JSON file", "error");
      }
    };
    reader.readAsText(file);
  };

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const availableModels = MODELS[newProvider] || MODELS.openrouter;
    setModelName(availableModels[0].value);
  };

  return (
    <div className="max-w-5xl mx-auto pb-32 animate-in fade-in duration-700">
      <ToastContainer />
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">Automation & AI</h1>
          <p className="text-slate-500 font-medium">Configure your bot's responses, AI brain, and website integration.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleSaveAll} disabled={saving}
            className="bg-slate-900 text-white px-8 py-3.5 rounded-2xl font-bold text-sm hover:bg-blue-600 disabled:opacity-50 shadow-xl shadow-slate-200 transition-all active:scale-95 flex items-center gap-2">
            {saving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Save All Settings"}
          </button>
        </div>
      </div>

      <div className="bg-slate-100/50 p-2 rounded-[2.5rem] mb-12 flex flex-col md:flex-row gap-2 border border-slate-200/50">
        {[
          { value: "default", label: "Smart Sales Flow", icon: "🚀", desc: "Automated site-sync" },
          { value: "predefined", label: "Keyword Engine", icon: "⌨️", desc: "Custom trigger rules" },
          { value: "ai", label: "AI Intelligence", icon: "🧠", desc: "LLM powered brain" },
        ].map(opt => (
          <button key={opt.value} onClick={() => setMode(opt.value)}
            className={`flex-1 flex items-center gap-4 p-4 rounded-[2rem] transition-all duration-300 ${mode === opt.value ? "bg-white shadow-lg ring-1 ring-slate-200" : "text-slate-500 hover:bg-white/50"}`}>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${mode === opt.value ? "bg-blue-600 text-white" : "bg-slate-200/50"}`}>
              {opt.icon}
            </div>
            <div className="text-left">
              <div className="font-bold text-sm">{opt.label}</div>
              <div className="text-[10px] font-bold opacity-60 uppercase tracking-widest">{opt.desc}</div>
            </div>
          </button>
        ))}
      </div>

      <div className="space-y-12">
        {mode === "ai" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 bg-white rounded-[3rem] border border-slate-200 p-10 space-y-6">
              <h2 className="text-2xl font-black text-slate-900">AI Personality & Context</h2>
              <textarea value={prompt} onChange={e => setPrompt(e.target.value)} rows={12}
                className="w-full bg-slate-50 border border-slate-200 rounded-[2.5rem] p-8 text-sm outline-none focus:bg-white focus:border-blue-500 transition-all resize-none" />
            </div>
            <div className="bg-white rounded-[3rem] p-10 border border-slate-200 space-y-6">
              <h3 className="text-xl font-black text-slate-900">Model Configuration</h3>
              <div className="space-y-4">
                <select value={provider} onChange={e => handleProviderChange(e.target.value)} className="w-full p-4 bg-slate-50 rounded-2xl border">
                  {Object.keys(MODELS).map(p => <option key={p} value={p}>{PROVIDER_INFO[p]?.label || p}</option>)}
                </select>
                <select value={modelName} onChange={e => setModelName(e.target.value)} className="w-full p-4 bg-slate-50 rounded-2xl border">
                  {(MODELS[provider] || []).map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
                <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="API Key" className="w-full p-4 bg-slate-50 rounded-2xl border" />
                <input type="range" min="0" max="100" value={temperature} onChange={e => setTemperature(parseInt(e.target.value))} className="w-full" />
                <div className="flex justify-between text-xs font-bold text-blue-600"><span>Creative: {temperature}%</span></div>
              </div>
            </div>
          </div>
        )}

        {mode === "default" && (
          <div className="space-y-8">
            <div className="bg-blue-600 rounded-[3rem] p-10 text-white">
              <h2 className="text-3xl font-black mb-3">Sales Journey Automation</h2>
              <p className="text-blue-100 font-medium">Customize templates and enable/disable specific menu options.</p>
            </div>

            {/* Menu Section Toggles */}
            <div className="bg-white rounded-[3rem] border border-slate-200 p-10">
              <h3 className="text-xl font-black text-slate-900 mb-6">📋 Menu Options</h3>
              <p className="text-slate-500 text-sm mb-6">Enable or disable specific menu items. Disabled options won't appear in the menu.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { id: 'services', label: 'Services', icon: 'ℹ️', defaultOn: false },
                  { id: 'order', label: 'Order Products', icon: '🛍️', defaultOn: true },
                  { id: 'product_list', label: 'Product Catalog', icon: '💰', defaultOn: true },
                  { id: 'delivery', label: 'Delivery Info', icon: '🚚', defaultOn: true },
                  { id: 'contact', label: 'Contact Us', icon: '📞', defaultOn: true },
                ].map((item) => {
                  const isEnabled = templateStatuses[`template_${item.id}_enabled`] ?? item.defaultOn;
                  return (
                    <div key={item.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{item.icon}</span>
                        <span className="font-bold text-sm text-slate-700">{item.label}</span>
                      </div>
                      <button
                        onClick={() => setTemplateStatuses({ ...templateStatuses, [`template_${item.id}_enabled`]: !isEnabled })}
                        className={`w-12 h-6 rounded-full transition-all relative ${isEnabled ? 'bg-green-500' : 'bg-slate-300'}`}
                      >
                        <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all shadow-sm ${isEnabled ? 'left-6' : 'left-0.5'}`} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Template Text Editors */}
            <div className="bg-white rounded-[3rem] border border-slate-200 p-10">
              <h3 className="text-xl font-black text-slate-900 mb-6">✏️ Template Messages</h3>
              <p className="text-slate-500 text-sm mb-6">Edit the text for each template. Leave empty to show nothing to users.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {templateConfigs.map((config) => {
                  const templateKey = `template_${config.id}`;
                  const isEnabled = templateStatuses[`${templateKey}_enabled`] ?? true;
                  const hasCustomContent = !!templates[templateKey];

                  return (
                    <div key={config.id} className={`bg-slate-50 rounded-[2.5rem] border p-8 flex flex-col ${!isEnabled && 'opacity-50'}`}>
                      <div className="flex justify-between items-center mb-4">
                        <h4 className="text-lg font-black text-slate-900">{config.name}</h4>
                        <button
                          onClick={() => setTemplateStatuses({ ...templateStatuses, [`${templateKey}_enabled`]: !isEnabled })}
                          className={`w-12 h-6 rounded-full transition-all relative ${isEnabled ? 'bg-green-500' : 'bg-slate-300'}`}
                        >
                          <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all shadow-sm ${isEnabled ? 'left-6' : 'left-0.5'}`} />
                        </button>
                      </div>
                      <textarea
                        disabled={!isEnabled}
                        value={templates[templateKey] || ""}
                        placeholder={config.placeholder}
                        onChange={(e) => setTemplates({ ...templates, [templateKey]: e.target.value })}
                        rows={6}
                        className="w-full bg-white border border-slate-200 rounded-2xl p-5 text-sm outline-none focus:border-blue-500 transition-all resize-none font-mono"
                      />
                      <div className="flex justify-between items-center mt-3">
                        {!hasCustomContent && isEnabled && (
                          <p className="text-[10px] text-amber-600 font-bold uppercase tracking-widest">⚠️ Using default message</p>
                        )}
                        {hasCustomContent && isEnabled && (
                          <p className="text-[10px] text-green-600 font-bold uppercase tracking-widest">✓ Custom message set</p>
                        )}
                        {!isEnabled && (
                          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Disabled</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {mode === "predefined" && (
          <div className="bg-white rounded-[3rem] border border-slate-200 p-10">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-10">
              <div>
                <h2 className="text-2xl font-black">Keyword Engine</h2>
                <p className="text-slate-500 text-sm">Set custom trigger words and their automatic responses.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <label className="cursor-pointer bg-slate-100 text-slate-700 px-6 py-3 rounded-2xl font-bold text-sm hover:bg-slate-200 transition-all flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                  Upload JSON
                  <input type="file" accept=".json" onChange={handleUploadJSON} className="hidden" />
                </label>
                <button onClick={handleDownloadJSON} className="bg-slate-100 text-slate-700 px-6 py-3 rounded-2xl font-bold text-sm hover:bg-slate-200 transition-all flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                  Download JSON
                </button>
                <button onClick={() => setCustomResponses([...customResponses, { keyword: "", response: "" }])} className="bg-slate-900 text-white px-6 py-3 rounded-2xl font-bold text-sm hover:bg-blue-600 transition-all">+ Create Rule</button>
              </div>
            </div>
            
            <div className="space-y-4">
              {customResponses.length === 0 ? (
                <div className="text-center py-20 bg-slate-50 rounded-[2rem] border-2 border-dashed border-slate-200">
                  <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">No custom rules yet</p>
                </div>
              ) : (
                customResponses.map((cr, idx) => (
                  <div key={idx} className="flex flex-col md:flex-row gap-4 p-6 bg-slate-50 rounded-[2rem] border border-slate-100 group hover:border-blue-200 transition-all">
                    <div className="flex-1 space-y-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-2">Trigger Keyword</label>
                      <input value={cr.keyword} onChange={e => {
                        const updated = [...customResponses];
                        updated[idx].keyword = e.target.value;
                        setCustomResponses(updated);
                      }} className="w-full p-4 rounded-xl border border-slate-200 outline-none focus:border-blue-500 font-bold text-sm" placeholder="e.g. price, promo, location" />
                    </div>
                    <div className="flex-[2] space-y-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-2">Bot Response</label>
                      <input value={cr.response} onChange={e => {
                        const updated = [...customResponses];
                        updated[idx].response = e.target.value;
                        setCustomResponses(updated);
                      }} className="w-full p-4 rounded-xl border border-slate-200 outline-none focus:border-blue-500 text-sm" placeholder="The message bot will send..." />
                    </div>
                    <div className="flex items-end pb-1">
                      <button onClick={() => setCustomResponses(customResponses.filter((_, i) => i !== idx))} className="w-12 h-12 flex items-center justify-center text-rose-500 hover:bg-rose-50 rounded-xl transition-all">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
