"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui";
import { useTheme } from "@/lib/useTheme";
import { LockedFeature } from "@/components/LockedFeature";
import { usePlanLimits } from "@/hooks/usePlanLimits";

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

const ALL_TEMPLATES = [
  { id: 'greeting', name: 'Greeting Message', placeholder: 'Hi {user_name}! Welcome to {site_name}. Type *menu* to see how I can help you today!', isFixed: false, defaultOn: false },
  { id: 'menu', name: 'Main Menu', placeholder: `*Main Menu*

1. Services
2. Delivery Info
3. Contact Us
4. Products
5. Place Order

Reply with a number to continue!`, isFixed: true, defaultOn: true },
  { id: 'services', name: 'Services', placeholder: `*Our Services*

Our services include:
• Web Development
• Mobile Apps
• UI/UX Design`, isFixed: false, defaultOn: true },
  { id: 'delivery', name: 'Delivery Info', placeholder: `*Delivery Information*

We offer fast nationwide delivery within 3-5 business days.`, isFixed: false, defaultOn: true },
  { id: 'contact', name: 'Contact Us', placeholder: `*Contact Us*

{site_name}
Phone: {phone}
Email: {email}
Address: {address}`, isFixed: false, defaultOn: true },
  { id: 'product', name: 'Product Text', placeholder: `*Our Products*

We sell high-quality shirts and apparel. Browse our collection and place your order!`, isFixed: false, defaultOn: true },
  { id: 'order_form', name: 'Order Form', placeholder: `*Order Form*

Please provide your order details in the format below:

Name:
Product:
Quantity:
Phone:
Address:

Once submitted, we will confirm your order shortly.`, isFixed: true, defaultOn: true },
  { id: 'order_confirmation', name: 'Order Confirmation', placeholder: `*Order Confirmed!*

Thank you for your order! We'll contact you soon to confirm delivery details.`, isFixed: false, defaultOn: true },
];

const TOGGLABLE_TEMPLATES = [
  { id: 'services', label: 'Services', icon: 'SV', defaultOn: true },
  { id: 'delivery', label: 'Delivery Info', icon: 'DL', defaultOn: true },
  { id: 'contact', label: 'Contact Us', icon: 'CT', defaultOn: true },
  { id: 'product', label: 'Products', icon: 'PR', defaultOn: true },
  { id: 'order_form', label: 'Order Form', icon: 'OF', defaultOn: true },
];

export default function SettingsPage() {
  const [bot, setBot] = useState<any>(null);
  const [settings, setSettings] = useState<any>(null);
  const [mode, setMode] = useState("default");
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("openrouter");
  const [customTemplates, setCustomTemplates] = useState<Array<{id?: number, template_name: string, content: string}>>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [userPlan, setUserPlan] = useState("free");
  const [orderFormTemplate, setOrderFormTemplate] = useState("");
  const [orderConfirmationMessage, setOrderConfirmationMessage] = useState("");
  const [orderFormEnabled, setOrderFormEnabled] = useState(true);
  const [formMenuLabel, setFormMenuLabel] = useState("");
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [hasApiKey, setHasApiKey] = useState(false);
  const [temperature, setTemperature] = useState(70);
  const [language, setLanguage] = useState("english");
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<Record<string, string>>({});
  const [templateEnabled, setTemplateEnabled] = useState(true);
  const [templateStatuses, setTemplateStatuses] = useState<Record<string, boolean>>({});
  const [customResponses, setCustomResponses] = useState<Array<{keyword: string, response: string}>>([]);
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [responseDelay, setResponseDelay] = useState(0);

  const { showToast, ToastContainer } = useToast();
  const { isDark } = useTheme();
  const templateConfigs = ALL_TEMPLATES;

  // Plan limits hook
  const { planLimits, canUseOrderForm, canAddTemplate, canAddRuleMessage, isFreePlan } = usePlanLimits();

  useEffect(() => {
    Promise.all([
      api("/api/bots/me").catch(() => null),
      api("/api/bots/settings").catch(() => null),
      api("/api/bots/custom-templates").catch(() => ({ templates: [] })),
      api("/api/bots/order-form/settings").catch(() => null),
    ]).then(([botData, settingsData, templatesData, orderFormData]) => {
      setBot(botData);
      if (botData) {
        setMode(botData.mode || "default");
      } else {
        setMode("default");
      }

      // Load custom templates
      if (templatesData && templatesData.templates) {
        setCustomTemplates(templatesData.templates);
      }

      // Load order form settings
      if (orderFormData) {
        setOrderFormTemplate(orderFormData.order_form_template || "");
        setOrderConfirmationMessage(orderFormData.order_confirmation_message || "");
        setOrderFormEnabled(orderFormData.order_form_enabled ?? true);
        setFormMenuLabel(orderFormData.form_menu_label || "");
      }

      const defaultProvider = "openrouter";
      const availableDefaultModels = MODELS[defaultProvider] || [];
      const defaultModel = availableDefaultModels.length > 0 ? availableDefaultModels[0].value : "";

      if (settingsData) {
        setSettings(settingsData);
        setPrompt(settingsData.prompt || "");
        const currentProvider = settingsData.model_name || defaultProvider;
        setProvider(currentProvider);
        const availableModels = MODELS[currentProvider] || MODELS[defaultProvider] || [];
        setModelName(settingsData.specific_model_name || (availableModels.length > 0 ? availableModels[0].value : defaultModel));
        setTemperature(settingsData.temperature === undefined ? 70 : settingsData.temperature);
        setLanguage(settingsData.language || "english");
        setHasApiKey(settingsData.has_api_key || false);

        const defaultStatuses: Record<string, boolean> = {};
        ALL_TEMPLATES.forEach(t => {
          defaultStatuses[`template_${t.id}_enabled`] = t.defaultOn ?? true;
        });
        const loadedStatuses = settingsData.template_statuses || {};
        setTemplateStatuses({ ...defaultStatuses, ...loadedStatuses });

        const loadedTemplates: Record<string, string> = {};
        try {
          const rawTemplates = settingsData.templates || {};
          if (rawTemplates && typeof rawTemplates === 'object') {
            Object.entries(rawTemplates).forEach(([key, value]) => {
              if (typeof value === 'string' && key.startsWith('template_') && !key.endsWith('_enabled')) {
                loadedTemplates[key] = value;
              }
            });
          }
        } catch (err) {
          console.error("Failed to parse templates:", err);
        }
        setTemplates(loadedTemplates);
        setTemplateEnabled(settingsData.template_enabled ?? true);

        let loadedCustomResponses: Array<{keyword: string, response: string}> = [];
        if (settingsData.custom_responses) {
          try {
            if (Array.isArray(settingsData.custom_responses)) {
              loadedCustomResponses = settingsData.custom_responses
                .filter((cr: any) => cr && cr.keyword && cr.keyword.trim())
                .map((cr: any) => ({
                  keyword: cr.keyword,
                  response: cr.response || cr.message || cr.reply || '',
                }));
            } else if (typeof settingsData.custom_responses === "object") {
              loadedCustomResponses = Object.entries(settingsData.custom_responses)
                .filter(([key, value]) => !key.startsWith('template_') && typeof value === 'string')
                .map(([keyword, response]) => ({
                  keyword: keyword,
                  response: response as string,
                }));
            }
          } catch (err) {
            console.error("Failed to parse custom_responses:", err);
          }
        }
        setCustomResponses(loadedCustomResponses);

        // Load WhatsApp engine settings
        setWelcomeMessage(settingsData.welcome_message || "");
        setResponseDelay(settingsData.response_delay || 0);

      } else {
        // Set sensible defaults if settingsData is null
        setPrompt("");
        setProvider(defaultProvider);
        setModelName(defaultModel);
        setTemperature(70);
        setLanguage("english");
        const defaultStatuses: Record<string, boolean> = {};
        ALL_TEMPLATES.forEach(t => {
          defaultStatuses[`template_${t.id}_enabled`] = t.defaultOn ?? true;
        });
        setTemplateStatuses(defaultStatuses);
        setTemplates({});
        setTemplateEnabled(true);
        setCustomResponses([]);
      }
    });

    // Fetch user plan
    api("/api/bots/me").then((botData) => {
      if (botData && botData.owner) {
        setUserPlan(botData.owner.plan || "free");
      }
    }).catch(() => {});
  }, []);

  // Refetch data when mode changes to prevent stale cache
  useEffect(() => {
    if (!bot) return; // Don't run on initial mount

    // Clear current data and refetch fresh data from database
    api("/api/bots/settings").then((settingsData) => {
      if (settingsData) {
        setSettings(settingsData);
        setPrompt(settingsData.prompt || "");
        const currentProvider = settingsData.model_name || "openrouter";
        setProvider(currentProvider);
        const availableModels = MODELS[currentProvider] || MODELS["openrouter"] || [];
        setModelName(settingsData.specific_model_name || (availableModels.length > 0 ? availableModels[0].value : ""));
        setTemperature(settingsData.temperature === undefined ? 70 : settingsData.temperature);
        setLanguage(settingsData.language || "english");
        setHasApiKey(settingsData.has_api_key || false);

        const defaultStatuses: Record<string, boolean> = {};
        ALL_TEMPLATES.forEach(t => {
          defaultStatuses[`template_${t.id}_enabled`] = t.defaultOn ?? true;
        });
        const loadedStatuses = settingsData.template_statuses || {};
        setTemplateStatuses({ ...defaultStatuses, ...loadedStatuses });

        const loadedTemplates: Record<string, string> = {};
        try {
          const rawTemplates = settingsData.templates || {};
          if (rawTemplates && typeof rawTemplates === 'object') {
            Object.entries(rawTemplates).forEach(([key, value]) => {
              if (typeof value === 'string' && key.startsWith('template_') && !key.endsWith('_enabled')) {
                loadedTemplates[key] = value;
              }
            });
          }
        } catch (err) {
          console.error("Failed to parse templates:", err);
        }
        setTemplates(loadedTemplates);
        setTemplateEnabled(settingsData.template_enabled ?? true);

        let loadedCustomResponses: Array<{keyword: string, response: string}> = [];
        if (settingsData.custom_responses) {
          try {
            if (Array.isArray(settingsData.custom_responses)) {
              loadedCustomResponses = settingsData.custom_responses
                .filter((cr: any) => cr && cr.keyword && cr.keyword.trim())
                .map((cr: any) => ({
                  keyword: cr.keyword,
                  response: cr.response || cr.message || cr.reply || '',
                }));
            } else if (typeof settingsData.custom_responses === "object") {
              loadedCustomResponses = Object.entries(settingsData.custom_responses)
                .filter(([key, value]) => !key.startsWith('template_') && typeof value === 'string')
                .map(([keyword, response]) => ({
                  keyword: keyword,
                  response: response as string,
                }));
            }
          } catch (err) {
            console.error("Failed to parse custom_responses:", err);
          }
        }
        setCustomResponses(loadedCustomResponses);

        // Load WhatsApp engine settings
        setWelcomeMessage(settingsData.welcome_message || "");
        setResponseDelay(settingsData.response_delay || 0);
      }
    }).catch(() => {});

    // Refetch custom templates
    api("/api/bots/custom-templates").then((templatesData) => {
      if (templatesData && templatesData.templates) {
        setCustomTemplates(templatesData.templates);
      }
    }).catch(() => {});

    // Refetch order form settings
    api("/api/bots/order-form/settings").then((orderFormData) => {
      if (orderFormData) {
        setOrderFormTemplate(orderFormData.order_form_template || "");
        setOrderConfirmationMessage(orderFormData.order_confirmation_message || "");
        setOrderFormEnabled(orderFormData.order_form_enabled ?? true);
        setFormMenuLabel(orderFormData.form_menu_label || "");
      }
    }).catch(() => {});
  }, [mode]); // Trigger when mode changes

  const handleSaveAll = async () => {
    console.log("Saving settings initiated...");
    setSaving(true);
    try {
      // Validate custom templates if in default mode
      if (mode === "default") {
        for (const template of customTemplates) {
          if (template.template_name && !template.template_name.trim()) {
            showToast("All templates must have a name", "error");
            setSaving(false);
            return;
          }
          if (template.template_name && template.template_name.length > 50) {
            showToast("Template names must be 50 characters or less", "error");
            setSaving(false);
            return;
          }
          if (template.content && !template.content.trim()) {
            showToast("All templates must have content", "error");
            setSaving(false);
            return;
          }
          if (template.content && template.content.length > 1000) {
            showToast("Template content must be 1000 characters or less", "error");
            setSaving(false);
            return;
          }
        }
      }

      // Enforce plan limits before saving
      if (planLimits) {
        // Check template limit
        const templateLimit = planLimits.limits.max_templates;
        if (templateLimit > 0) { // 0 means unlimited
          // templates object has 'template_ID' keys. Count those that have content and are not '_enabled'
          const customizedTemplatesCount = Object.entries(templates).filter(([k, v]) => 
            k.startsWith('template_') && !k.endsWith('_enabled') && v && v.trim() !== ""
          ).length;

          // Also add custom templates count
          const totalTemplates = customizedTemplatesCount + customTemplates.length;

          if (totalTemplates > templateLimit) {
            showToast(`Template limit reached (${totalTemplates}/${templateLimit}). Upgrade to add more.`, "error");
            setSaving(false);
            return;
          }
        }

        // Check rule message limit
        const ruleLimit = planLimits.limits.max_rule_based_messages;
        if (ruleLimit > 0) {
          const ruleCount = customResponses.filter(cr => cr.keyword.trim()).length;
          if (ruleCount > ruleLimit) {
            showToast(`Rule limit reached (${ruleCount}/${ruleLimit}). Upgrade to add more.`, "error");
            setSaving(false);
            return;
          }
        }
      }

      // Convert custom responses array to object/dictionary for backend
      const customResponsesPayload = customResponses
        .filter(cr => cr.keyword.trim()) // Ensure keyword is not empty
        .reduce((acc, cr) => {
          acc[cr.keyword.trim().toLowerCase()] = cr.response;
          return acc;
        }, {} as Record<string, string>);

      const payload: Record<string, any> = {
        prompt,
        model_name: provider,
        specific_model_name: modelName,
        temperature,
        language,
        custom_responses: customResponsesPayload, // Send as object/dictionary
        templates,
        template_enabled: templateEnabled,
        template_statuses: templateStatuses,
        welcome_message: welcomeMessage,
        response_delay: responseDelay,
      };
      // Only send API key if user entered a new one
      if (apiKey && apiKey.trim()) {
        payload.api_key = apiKey;
      }
      console.log("Payload before sending:", JSON.stringify(payload, null, 2));

      // Save custom templates if in default mode
      if (mode === "default") {
        for (const template of customTemplates) {
          if (template.id) {
            // Update existing template
            await api(`/api/bots/custom-templates/${template.id}`, {
              method: "PUT",
              body: JSON.stringify({
                template_name: template.template_name,
                content: template.content
              })
            });
          } else if (template.template_name && template.content) {
            // Create new template only if both name and content exist
            const result = await api("/api/bots/custom-templates", {
              method: "POST",
              body: JSON.stringify({
                template_name: template.template_name,
                content: template.content
              })
            });
            // Update local state with new ID
            template.id = result.id;
          }
        }
      }

      console.log("Sending API requests to /api/bots/mode, /api/bots/settings, and /api/bots/order-form/settings...");

      // Save all settings sequentially to ensure proper order
      await api("/api/bots/mode", { method: "PATCH", body: JSON.stringify({ mode }) });
      console.log("✓ Bot mode saved");

      await api("/api/bots/settings", {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      console.log("✓ Bot settings saved");

      await api("/api/bots/order-form/settings", {
        method: "PUT",
        body: JSON.stringify({
          order_form_template: orderFormTemplate,
          order_confirmation_message: orderConfirmationMessage,
          order_form_enabled: orderFormEnabled,
          form_menu_label: formMenuLabel
        })
      });
      console.log("✓ Order form settings saved");

      // Wait a moment to ensure database commits
      await new Promise(resolve => setTimeout(resolve, 500));

      // Dispatch custom event to notify other pages about bot mode change
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('botModeChanged', { detail: { mode } }));
      }

      console.log("Fetching updated settings and bot data...");
      const [updatedSettings, updatedBot] = await Promise.all([
        api("/api/bots/settings"),
        api("/api/bots/me")
      ]);
      setSettings(updatedSettings);
      setBot(updatedBot);

      // Update hasApiKey flag and clear the input field
      if (apiKey && apiKey.trim()) {
        setHasApiKey(true);
        setApiKey(""); // Clear the field after successful save
      } else {
        setHasApiKey(updatedSettings.has_api_key || false);
      }

      console.log("Updated settings and bot data fetched.");

      let reloadedResponses: Array<{keyword: string, response: string}> = [];
      if (updatedSettings.custom_responses && typeof updatedSettings.custom_responses === "object") {
        reloadedResponses = Object.entries(updatedSettings.custom_responses)
          .filter(([key, value]) => !key.startsWith('template_') && typeof value === 'string')
          .map(([keyword, response]) => ({
            keyword,
            response: response as string,
          }));
      } else if (Array.isArray(updatedSettings.custom_responses)) {
        reloadedResponses = updatedSettings.custom_responses
          .filter((cr: any) => cr && cr.keyword && cr.keyword.trim())
          .map((cr: any) => ({
            keyword: cr.keyword,
            response: cr.response || cr.message || cr.reply || '',
          }));
      }
      setCustomResponses(reloadedResponses);
      setHasUnsavedChanges(false);
      console.log("Custom responses reloaded.");
      showToast("All settings saved successfully! ✓", "success");
      console.log("Settings saved successfully!");
    } catch (err: any) {
      console.error("Error during save operation:", err.message || "Failed to save settings", err);
      showToast("Error: " + (err.message || "Failed to save settings"), "error");
    } finally {
      setSaving(false);
      console.log("Saving operation finished.");
    }
  };

  const handleDownloadJSON = () => {
    const data = customResponses.reduce((acc, cr) => {
      if (cr.keyword.trim()) {
        acc[cr.keyword.trim()] = cr.response;
      }
      return acc;
    }, {} as Record<string, string>);

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bot-rules-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadSample = () => {
    // Download the sample JSON file from public folder
    const a = document.createElement("a");
    a.href = "/sample-bot-rules.json";
    a.download = "sample-bot-rules.json";
    a.click();
  };

  const handleUploadJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.json')) {
      showToast("Please select a valid JSON file", "error");
      e.target.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        let newCustomResponses: Array<{ keyword: string; response: string }> = [];

        // Format 1: Array of objects with keyword/response pairs
        if (Array.isArray(json)) {
          newCustomResponses = json
            .filter((item: any) => item && typeof item === 'object')
            .map((item: any) => {
              const keyword = item.keyword || item.trigger || item.key || '';
              const response = item.response || item.message || item.reply || item.answer || '';
              return { keyword: keyword.trim(), response };
            })
            .filter((cr) => cr.keyword && cr.response);
        }
        // Format 2: Object with custom_responses property (array)
        else if (Array.isArray(json.custom_responses)) {
          newCustomResponses = json.custom_responses
            .filter((cr: any) => cr && typeof cr === 'object')
            .map((cr: any) => {
              const keyword = cr.keyword || cr.trigger || cr.key || '';
              const response = cr.response || cr.message || cr.reply || cr.answer || '';
              return { keyword: keyword.trim(), response };
            })
            .filter((cr: { keyword: string; response: string }) => cr.keyword && cr.response);
        }
        // Format 3: Object with custom_responses property (object)
        else if (json.custom_responses && typeof json.custom_responses === 'object' && !Array.isArray(json.custom_responses)) {
          newCustomResponses = Object.entries(json.custom_responses)
            .filter(([key, value]) => key && !key.startsWith('template_') && typeof value === 'string' && value.trim())
            .map(([keyword, response]) => ({ keyword: keyword.trim(), response: response as string }));
        }
        // Format 4: Simple key-value object at root level (most common)
        else if (json && typeof json === 'object' && !Array.isArray(json)) {
          newCustomResponses = Object.entries(json)
            .filter(([key, value]) => {
              // Skip metadata fields and template fields
              const skipKeys = ['mode', 'templates', 'template_enabled', 'template_statuses', 'language', 'model_name', 'temperature', 'custom_responses'];
              return key && !key.startsWith('template_') && !skipKeys.includes(key) && typeof value === 'string' && value.trim();
            })
            .map(([keyword, response]) => ({ keyword: keyword.trim(), response: response as string }));
        }

        if (newCustomResponses.length > 0) {
          setCustomResponses(newCustomResponses);
          showToast(`Successfully imported ${newCustomResponses.length} rules!`, "success");
        } else {
          showToast("No valid rules found in the JSON file. Please check the format.", "error");
        }
        e.target.value = '';
      } catch (err) {
        console.error("JSON parse error:", err);
        showToast("Invalid JSON format. Please check your file.", "error");
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const availableModels = MODELS[newProvider] || MODELS["openrouter"] || [];
    setModelName(availableModels.length > 0 ? availableModels[0].value : "");
  };

  // Get plan limits based on user plan
  const handleAddTemplate = () => {
    const limit = planLimits?.limits.max_templates || 0;

    // Check current UI state count against limit
    // 0 means unlimited (premium plan)
    if (limit > 0 && customTemplates.length >= limit) {
      showToast(
        `Template limit reached (${customTemplates.length}/${limit}). Upgrade to add more.`,
        "warning"
      );
      return;
    }

    setCustomTemplates([...customTemplates, { template_name: "", content: "" }]);
    setHasUnsavedChanges(true);
  };

  const handleAddCustomResponse = () => {
    const limit = planLimits?.limits.max_rule_based_messages || 0;

    // Check current UI state count against limit
    // 0 means unlimited (premium plan)
    if (limit > 0 && customResponses.length >= limit) {
      showToast(
        `Rule limit reached (${customResponses.length}/${limit}). Upgrade to add more.`,
        "warning"
      );
      return;
    }

    setCustomResponses([...customResponses, { keyword: "", response: "" }]);
    setHasUnsavedChanges(true);
  };

  const handleUpdateTemplate = (index: number, field: "template_name" | "content", value: string) => {
    const updated = [...customTemplates];
    updated[index][field] = value;
    setCustomTemplates(updated);
    setHasUnsavedChanges(true);
  };

  const handleDeleteTemplate = async (index: number) => {
    const template = customTemplates[index];

    if (!confirm("Delete this template? It will be removed from your bot menu.")) {
      return;
    }

    // If template has an ID, delete from backend
    if (template.id) {
      try {
        await api(`/api/bots/custom-templates/${template.id}`, { method: "DELETE" });
        showToast("Template deleted successfully!", "success");
      } catch (err: any) {
        showToast(err.message || "Failed to delete template", "error");
        return;
      }
    }

    // Remove from local state
    setCustomTemplates(customTemplates.filter((_, i) => i !== index));
    setHasUnsavedChanges(true);
  };


  return (
    <div className="max-w-5xl mx-auto pb-32 animate-in fade-in duration-700">
      <ToastContainer />

      <div className="mb-12">
        <h1 className={`text-4xl font-bold tracking-tighter mb-2 ${isDark ? "text-white" : "text-slate-900"}`}>Bot Settings</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-medium`}>Configure your bot's conversational style and behavior.</p>

        {/* Active Bot Mode Badge - Read-only */}
        {bot && (
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full border" style={{
            backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.1)',
            borderColor: isDark ? 'rgba(34, 197, 94, 0.3)' : 'rgba(34, 197, 94, 0.3)'
          }}>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className={`text-sm font-medium ${isDark ? "text-green-400" : "text-green-700"}`}>
              {bot.mode === "default" ? "Build Your Own Reply Templates" :
               bot.mode === "predefined" ? "Reply to Specific Words" :
               bot.mode === "ai" ? "Dynamic AI Conversations" :
               "No mode selected"}
            </span>
          </div>
        )}
      </div>

      <div className={`p-2.5 rounded-[3rem] mb-12 flex flex-col md:flex-row gap-2.5 border ${isDark ? "bg-[#050505] border-zinc-800" : "bg-slate-100/50 border-slate-200/50"}`}>
        {[
          { value: "default", label: "Customize Flow Mode", desc: "Build your own reply templates" },
          { value: "predefined", label: "Keyword Trigger Mode", desc: "Reply to specific words" },
          { value: "ai", label: "Dynamic AI Mode", desc: "Dynamic AI Conversations" },
        ].map(opt => (
          <button key={opt.value} onClick={() => {
            if (hasUnsavedChanges && mode === "default") {
              if (!confirm("You have unsaved changes. Save before switching?")) {
                return;
              }
            }
            setMode(opt.value);
          }}
            className={`flex-1 flex items-center gap-5 p-5 rounded-[2.5rem] transition-all duration-500 relative ${mode === opt.value ? isDark ? "bg-[#121212] text-white shadow-2xl shadow-black" : "bg-white shadow-lg ring-1 ring-slate-200" : isDark ? "text-zinc-500 hover:bg-white/5 hover:text-white" : "text-slate-500 hover:bg-white/50"}`}>
            {bot?.mode === opt.value && (
              <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-[9px] font-bold uppercase tracking-wide text-green-600">Active</span>
              </div>
            )}
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-black transition-all duration-500 ${mode === opt.value ? (isDark ? "bg-white text-black" : "bg-black text-white") : isDark ? "bg-zinc-900 text-zinc-600" : "bg-slate-200/50 text-slate-400"}`}>
              {opt.value === "default" ? "CF" : opt.value === "predefined" ? "KW" : "AI"}
            </div>
            <div className="text-left">
              <div className={`font-bold text-sm tracking-tight ${mode === opt.value ? (isDark ? "text-white" : "text-slate-900") : "inherit"}`}>{opt.label}</div>
              <div className={`text-[9px] font-bold uppercase tracking-wide mt-1 ${mode === opt.value ? (isDark ? "text-zinc-500" : "text-slate-500") : "text-zinc-600"}`}>{opt.desc}</div>
            </div>
          </button>
        ))}
      </div>

      <div className="space-y-12">
        {mode === "ai" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className={`lg:col-span-2 rounded-[3rem] border p-12 space-y-8 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
              <h2 className={`text-2xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>AI Persona & Knowledge</h2>
              <textarea value={prompt} onChange={e => setPrompt(e.target.value)}
                className="textarea-field" rows={14}
                placeholder="Describe how your bot should behave, its tone, and specialized knowledge for interacting with customers..." />
            </div>
            <div className={`rounded-[3rem] p-12 border space-y-8 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
              <h3 className={`text-xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Model Configuration</h3>
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-wide text-zinc-600 ml-1">AI Provider</label>
                  <select value={provider} onChange={e => handleProviderChange(e.target.value)} className="select-field">
                    {Object.keys(MODELS).map(p => <option key={p} value={p}>{PROVIDER_INFO[p]?.label || p}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-wide text-zinc-600 ml-1">Choose Model</label>
                  <select value={modelName} onChange={e => setModelName(e.target.value)} className="select-field">
                    {(MODELS[provider] || MODELS["openrouter"] || []).map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-wide text-zinc-600 ml-1">API Key</label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder={hasApiKey ? "••••••••••••••••••••••••••••" : "Enter your API key here..."}
                    className="input-field"
                  />
                  {hasApiKey && (
                    <p className="text-[9px] font-medium text-green-600 px-1">
                      ✓ API key is saved. Leave blank to keep current key, or enter a new one to update.
                    </p>
                  )}
                </div>
                <div className="space-y-4 pt-4">
                  <div className="flex justify-between text-[10px] font-bold uppercase tracking-wide text-zinc-500 px-1">
                    <span>Serious</span>
                    <span>Creative</span>
                  </div>
                  <input type="range" min="0" max="100" value={temperature} onChange={e => setTemperature(parseInt(e.target.value))} className={`w-full h-1.5 rounded-full appearance-none cursor-pointer ${isDark ? "bg-zinc-800 accent-white" : "bg-slate-200 accent-slate-600"}`} />
                  <div className={`text-center text-[10px] font-bold uppercase tracking-wide ${isDark ? "text-white" : "text-slate-600"}`}>Creativity Level: {temperature}%</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {mode === "default" && (
          <div className="space-y-10">
            <div className={`rounded-[3rem] p-12 shadow-2xl ${isDark ? "bg-white text-black" : "bg-slate-900 text-white"}`}>
              <h2 className="text-4xl font-bold tracking-tighter mb-4">Customize Flow Mode</h2>
              <p className={`font-medium max-w-xl ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Build your own reply templates. Your brand, your words.</p>
            </div>

            <div className={`rounded-[3rem] border p-12 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
              <h3 className={`text-2xl font-bold tracking-tight mb-8 ${isDark ? "text-white" : "text-slate-900"}`}>Greeting & Submission Templates</h3>

              <div className="space-y-10">
                <div className="space-y-4">
                  <h4 className={`text-lg font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Greeting Message</h4>
                  <p className={`text-sm font-medium ${isDark ? "text-zinc-600" : "text-slate-500"}`}>The first message customers see when they contact you.</p>
                  <textarea
                    value={templates["template_greeting"] || ""}
                    placeholder="Hi {user_name}! Welcome to {site_name}. Type *menu* to see how I can help you today!"
                    onChange={(e) => setTemplates({ ...templates, "template_greeting": e.target.value })}
                    rows={4}
                    className="textarea-field"
                  />
                </div>

                <div className={`h-px ${isDark ? "bg-zinc-800" : "bg-slate-200"}`}></div>

                <LockedFeature
                  isLocked={!canUseOrderForm()}
                  featureName="Order Form"
                  requiredPlan="STARTER or PREMIUM"
                  className="space-y-6"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className={`text-lg font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Form Submission</h4>
                      <p className={`text-sm font-medium mt-1 ${isDark ? "text-zinc-600" : "text-slate-500"}`}>Edit the form your customers receive on WhatsApp. Customers fill and reply with their details in one message.</p>
                    </div>
                    <button
                      onClick={() => {
                        if (!canUseOrderForm()) {
                          showToast("Order Form is locked on FREE plan. Upgrade to unlock.", "error");
                          return;
                        }
                        setOrderFormEnabled(!orderFormEnabled);
                        setHasUnsavedChanges(true);
                      }}
                      className={`w-12 h-6 rounded-full transition-all relative ${orderFormEnabled ? (isDark ? 'bg-white' : 'bg-[#6c4ef2]') : (isDark ? 'bg-zinc-800' : 'bg-slate-300')}`}
                    >
                      <div className={`absolute top-0.5 w-5 h-5 rounded-full transition-all shadow-sm ${orderFormEnabled ? (isDark ? 'left-6 bg-black' : 'left-6 bg-white') : 'left-0.5 bg-zinc-600'}`} />
                    </button>
                  </div>

                  <div className="space-y-3 mt-6">
                    <label className={`text-[10px] font-bold uppercase tracking-wide px-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Submission Form Name</label>
                    <input
                      type="text"
                      value={formMenuLabel}
                      onChange={(e) => {
                        setFormMenuLabel(e.target.value);
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="e.g. Order, Appointment, Request, Booking..."
                      maxLength={30}
                      className="input-field"
                      disabled={!canUseOrderForm()}
                    />
                    <p className={`text-[9px] font-medium px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                      This is how this option appears in your WhatsApp menu. {formMenuLabel.length}/30 characters
                    </p>
                  </div>

                  <div className="space-y-3">
                    <label className={`text-[10px] font-bold uppercase tracking-wide px-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Form Submission Template</label>
                    <textarea
                      value={orderFormTemplate}
                      onChange={(e) => {
                        setOrderFormTemplate(e.target.value);
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="🛍️ Order Form&#10;&#10;Please fill in the details below and reply:&#10;&#10;Full Name:&#10;Phone Number:&#10;Delivery Address:&#10;Product / Item:&#10;Quantity:&#10;Special Instructions (optional):"
                      maxLength={1000}
                      rows={12}
                      className="textarea-field"
                      disabled={!canUseOrderForm()}
                    />
                    <p className={`text-[9px] font-medium px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                      {orderFormTemplate.length}/1000 characters
                    </p>
                  </div>

                  <div className="space-y-3">
                    <label className={`text-[10px] font-bold uppercase tracking-wide px-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Submission Confirmation Message</label>
                    <textarea
                      value={orderConfirmationMessage}
                      onChange={(e) => {
                        setOrderConfirmationMessage(e.target.value);
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="✅ Thank you! Your order has been received.&#10;Our team will contact you shortly to confirm."
                      maxLength={500}
                      rows={4}
                      className="textarea-field"
                      disabled={!canUseOrderForm()}
                    />
                    <p className={`text-[9px] font-medium px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                      {orderConfirmationMessage.length}/500 characters
                    </p>
                  </div>
                </LockedFeature>
              </div>
            </div>

            <div className={`rounded-[3rem] border p-12 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h3 className={`text-xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Smart Template Builder</h3>
                  <p className={`text-sm font-medium mt-1 ${isDark ? "text-zinc-600" : "text-slate-500"}`}>Create custom reply templates. Each template becomes a menu option for your customers on WhatsApp automatically.</p>
                </div>
                <button onClick={handleAddTemplate} className="btn-success py-2">+ Add Template</button>
              </div>

              <div className="space-y-6">
                {customTemplates.length === 0 ? (
                  <div className={`text-center py-24 rounded-[3rem] border-2 border-dashed ${isDark ? "bg-black border-zinc-800" : "bg-slate-50 border-slate-200"}`}>
                    <p className={`${isDark ? "text-zinc-600" : "text-slate-400"} font-medium text-sm`}>No templates yet. Click + Add Template to create your first one.</p>
                    <p className={`${isDark ? "text-zinc-700" : "text-slate-400"} text-xs mt-2`}>Your customers will see these as reply options.</p>
                  </div>
                ) : (
                  customTemplates.map((template, idx) => (
                    <div key={idx} className={`rounded-[2.5rem] border p-10 transition-all duration-300 ${isDark ? "bg-black border-zinc-800 hover:border-zinc-700" : "bg-slate-50 border-slate-100 hover:border-slate-200"}`}>
                      <div className="flex justify-between items-start mb-6">
                        <div className="flex-1 space-y-4">
                          <div className="space-y-2">
                            <label className={`text-[10px] font-bold uppercase tracking-wide px-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Template Name</label>
                            <input
                              value={template.template_name}
                              onChange={(e) => handleUpdateTemplate(idx, "template_name", e.target.value)}
                              placeholder="e.g., Services, Pricing, Contact Info"
                              maxLength={50}
                              className="input-field"
                            />
                            <p className={`text-[9px] font-medium px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                              {template.template_name.length}/50 characters
                            </p>
                          </div>
                          <div className="space-y-2">
                            <label className={`text-[10px] font-bold uppercase tracking-wide px-1 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Reply Content</label>
                            <textarea
                              value={template.content}
                              onChange={(e) => handleUpdateTemplate(idx, "content", e.target.value)}
                              placeholder="Type the message customers will receive when they select this option..."
                              maxLength={1000}
                              rows={6}
                              className="textarea-field"
                            />
                            <p className={`text-[9px] font-medium px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                              {template.content.length}/1000 characters
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteTemplate(idx)}
                          className={`ml-6 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${isDark ? "bg-zinc-900 hover:bg-red-900 text-zinc-400 hover:text-red-400" : "bg-slate-200 hover:bg-red-100 text-slate-600 hover:text-red-600"}`}
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {customTemplates.length > 0 && (
                <div className="mt-8 flex justify-center">
                  <button onClick={handleAddTemplate} className="btn-secondary py-2">+ Add New Template</button>
                </div>
              )}
            </div>
          </div>
        )}

        {mode === "predefined" && (
          <div className={`rounded-[3rem] border p-12 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-12">
              <div>
                <h2 className={`text-2xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Keyword Rules</h2>
                <p className={`text-sm font-medium mt-1 ${isDark ? "text-zinc-600" : "text-slate-500"}`}>Set automatic replies for specific words.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button onClick={handleDownloadSample} className="btn-secondary py-2">
                  Sample
                </button>
                <label className="btn-secondary py-2 cursor-pointer">
                  Upload JSON
                  <input type="file" accept=".json" onChange={handleUploadJSON} className="hidden" />
                </label>
                <button onClick={handleAddCustomResponse} className="btn-success py-2">+ New Rule</button>
              </div>
            </div>

            <div className="space-y-6">
              {customResponses.length === 0 ? (
                <div className={`text-center py-24 rounded-[3rem] border-2 border-dashed ${isDark ? "bg-black border-zinc-800" : "bg-slate-50 border-slate-200"}`}>
                  <p className={`${isDark ? "text-zinc-800" : "text-slate-400"} font-bold uppercase tracking-[0.3em] text-[10px]`}>No Rules Defined</p>
                </div>
              ) : (
                customResponses.map((cr, idx) => (
                  <div key={idx} className={`flex flex-col lg:flex-row gap-6 p-8 rounded-[2.5rem] border transition-all duration-300 ${isDark ? "bg-black border-zinc-800 hover:border-zinc-700" : "bg-slate-50 border-slate-100 hover:border-slate-200"}`}>
                    <div className="flex-1 space-y-3">
                      <label className={`text-[9px] font-bold uppercase tracking-[0.2em] px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>User Keyword</label>
                      <input value={cr.keyword} onChange={e => {
                        const updated = [...customResponses];
                        updated[idx].keyword = e.target.value;
                        setCustomResponses(updated);
                      }} className="input-field" placeholder="Enter trigger keyword (e.g. support, help)" />
                    </div>
                    <div className="flex-[2] space-y-3">
                      <label className={`text-[9px] font-bold uppercase tracking-[0.2em] px-1 ${isDark ? "text-zinc-700" : "text-slate-400"}`}>Automated Response</label>
                      <input value={cr.response} onChange={e => {
                        const updated = [...customResponses];
                        updated[idx].response = e.target.value;
                        setCustomResponses(updated);
                      }} className="input-field" placeholder="Type the automated response message..." />
                    </div>
                    <div className="flex items-end lg:pb-1">
                      <button onClick={() => setCustomResponses(customResponses.filter((_, i) => i !== idx))} className="btn-icon text-rose-500 hover:text-rose-600">
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

      <div className="mt-16 flex justify-end">
        <button onClick={handleSaveAll} disabled={saving}
          className="btn-primary min-w-[220px]">
          {saving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Save All Settings"}
        </button>
      </div>
    </div>
  );
}
