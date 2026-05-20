"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useToast } from "@/components/ui";
import { useTheme } from "@/lib/useTheme";

interface Usage {
  plan: string;
  whatsapp_messages_sent: number;
  whatsapp_limit: number;
  ai_requests_made: number;
  ai_limit: number;
  conversations_count: number;
  reset_date?: string;
}

const PLANS = {
  free: {
    name: "Free",
    price: "$0",
    period: "/month",
    color: "zinc",
    features: [
      { text: "WhatsApp Bot Access", included: true },
      { text: "3 Custom Templates", included: true },
      { text: "3 Rule-Based Messages", included: true },
      { text: "5 AI Responses / session", included: true },
      { text: "Basic Website Content Fetch", included: true },
      { text: "Up to 200 Conversations/Month", included: true },
      { text: "Basic Lead Capture", included: true },
      { text: "Basic Dashboard", included: true },
      { text: "Email Support", included: true },
      { text: "Product-based Flows", included: false },
      { text: "Order Form", included: false },
      { text: "WooCommerce Integration", included: false },
      { text: "Product Listing / Search", included: false },
      { text: "Live Chat Takeover", included: false },
      { text: "Multi-language Support", included: false },
      { text: "Advanced Analytics", included: false },
      { text: "User Tagging", included: false },
      { text: "Broadcast Campaigns", included: false },
    ],
  },
  starter: {
    name: "Starter",
    price: "$9.99",
    period: "/month",
    color: "amber",
    features: [
      { text: "Everything in Free Plan", included: true },
      { text: "10 Custom Templates", included: true },
      { text: "10 Rule-Based Messages", included: true },
      { text: "Unlimited AI Responses", included: true },
      { text: "Order Form Enabled", included: true },
      { text: "Product + Service Flows (Both)", included: true },
      { text: "WooCommerce (100 Products)", included: true },
      { text: "Product Listing + Search", included: true },
      { text: "Up to 1000 Conversations/Month", included: true },
      { text: "Multi-AI (Gemini, Claude)", included: true },
      { text: "User Tagging", included: true },
      { text: "Advanced Dashboard", included: false },
      { text: "Priority Support", included: false },
    ],
  },
  premium: {
    name: "Premium",
    price: "Contact",
    period: "Sales",
    color: "emerald",
    popular: true,
    features: [
      { text: "Everything in Starter", included: true },
      { text: "Unlimited Templates", included: true },
      { text: "Unlimited Rule Messages", included: true },
      { text: "Product + Service Flows (Full)", included: true },
      { text: "WooCommerce (Unlimited)", included: true },
      { text: "Product Listing (Unlimited)", included: true },
      { text: "Full Website Content Fetch", included: true },
      { text: "Up to 5000 Conversations/Month", included: true },
      { text: "Advanced Dashboard", included: true },
      { text: "Multi-language Support", included: true },
      { text: "Live Chat Takeover", included: true },
      { text: "Priority Support", included: true },
    ],
  },
};

export default function SubscriptionPage() {
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const { showToast, ToastContainer } = useToast();
  const { isDark } = useTheme();

  useEffect(() => {
    apiGet<Usage>("/api/auth/usage")
      .then((data) => {
        setUsage(data);
      })
      .catch((err) => {
        console.error("Failed to fetch usage:", err);
        showToast("Failed to load subscription data.", "error");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (targetPlan: "starter" | "premium") => {
    setUpgrading(true);
    try {
      await apiPost("/api/auth/upgrade-plan", { plan: targetPlan });
      showToast(`Successfully upgraded to ${targetPlan}!`, "success");
      const newData = await apiGet<Usage>("/api/auth/usage");
      setUsage(newData);
    } catch (err: any) {
      showToast(err.message || "Failed to upgrade plan.", "error");
    } finally {
      setUpgrading(false);
    }
  };

  const handleDowngradeTo = async (targetPlan: "free" | "starter") => {
    if (!confirm(`Are you sure? Paid features will be disabled.`)) return;
    setDowngrading(true);
    try {
      await apiPost("/api/auth/downgrade-plan", { plan: targetPlan });
      showToast(`Downgraded to ${targetPlan} plan.`, "success");
      const newData = await apiGet<Usage>("/api/auth/usage");
      setUsage(newData);
    } catch (err: any) {
      showToast(err.message || "Failed to downgrade.", "error");
    } finally {
      setDowngrading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className={`w-16 h-16 border-4 rounded-full animate-spin mx-auto mb-4 ${isDark ? "border-zinc-800" : "border-slate-100"}`} style={{ borderTopColor: isDark ? 'white' : 'black' }}></div>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-400"} font-black uppercase tracking-[0.2em] text-[10px]`}>Loading Account Data...</p>
        </div>
      </div>
    );
  }

  const currentPlan = usage?.plan || "free";
  const resetDate = usage?.reset_date
    ? new Date(usage.reset_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : 'End of billing cycle';

  return (
    <div className="space-y-12 max-w-7xl mx-auto pb-24 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <ToastContainer />

      {/* Header */}
      <div className="text-center max-w-2xl mx-auto">
        <h1 className={`text-5xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Subscription Plans</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-medium mt-4`}>Choose a plan that fits your business needs with simple, transparent pricing.</p>
        {currentPlan && (
          <div className={`mt-8 inline-flex items-center gap-3 px-6 py-2.5 rounded-2xl border ${isDark ? "bg-[#090909] border-zinc-800" : "bg-slate-50 border-slate-200"}`}>
            <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Current Plan:</span>
            <span className={`text-xs font-black uppercase tracking-widest ${
              currentPlan === 'free' ? (isDark ? 'text-white' : 'text-slate-900') :
              currentPlan === 'starter' ? 'text-amber-500' : 'text-emerald-500'
            }`}>
              {currentPlan}
            </span>
            <span className={`w-1 h-1 rounded-full ${isDark ? "bg-zinc-800" : "bg-slate-300"}`}></span>
            <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-500" : "text-slate-500"}`}>{resetDate}</span>
          </div>
        )}
      </div>

      {/* Current Usage */}
      {usage && (
        <div className={`rounded-[3rem] border shadow-2xl p-10 max-w-4xl mx-auto ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-slate-100"}`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="space-y-4">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>WhatsApp Messaging</p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>{usage.whatsapp_messages_sent} <span className="text-zinc-700 text-xl">/</span> {usage.whatsapp_limit}</p>
              <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                <div className={`h-full transition-all duration-1000 ${isDark ? "bg-white" : "bg-[#6c4ef2]"}`} style={{ width: `${Math.min((usage.whatsapp_messages_sent / usage.whatsapp_limit) * 100, 100)}%` }}></div>
              </div>
            </div>
            <div className="space-y-4">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>AI Processing</p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>{usage.ai_requests_made} <span className="text-zinc-700 text-xl">/</span> {usage.ai_limit}</p>
              <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                <div className={`h-full transition-all duration-1000 ${isDark ? "bg-zinc-400" : "bg-emerald-500"}`} style={{ width: `${Math.min((usage.ai_requests_made / usage.ai_limit) * 100, 100)}%` }}></div>
              </div>
            </div>
            <div className="space-y-4 text-center md:text-left">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Total Conversations</p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>{usage.conversations_count || 0}</p>
              <p className={`text-[9px] font-black uppercase tracking-widest ${isDark ? "text-zinc-700" : "text-slate-500"}`}>Total messages this billing cycle</p>
            </div>
          </div>
        </div>
      )}

      {/* Plan Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {Object.entries(PLANS).map(([key, plan]) => {
          const isCurrent = currentPlan === key;
          return (
            <div key={key} className={`rounded-[3rem] p-10 border-2 transition-all duration-500 relative flex flex-col ${
              isDark 
                ? (isCurrent ? 'bg-[#0F0F0F] border-white/20 shadow-2xl shadow-black' : 'bg-[#090909] border-zinc-800 hover:border-zinc-700') 
                : (isCurrent ? 'bg-white border-blue-600 shadow-2xl shadow-blue-50' : 'bg-white border-slate-100 hover:border-slate-200')
            }`}>
              {plan.popular && !isCurrent && (
                <div className="absolute top-0 right-10 bg-white text-black px-4 py-1.5 text-[9px] font-black uppercase tracking-widest rounded-b-xl shadow-xl">
                  Most Popular
                </div>
              )}
              {isCurrent && (
                <div className={`absolute top-6 right-8 px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${isDark ? "bg-white text-black" : "bg-[#6c4ef2] text-white"}`}>
                  Current
                </div>
              )}
              
              <div className="mb-10">
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-5xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>{plan.price}</span>
                  <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>{plan.period}</span>
                </div>
                <h3 className={`text-xl font-black uppercase tracking-tight ${isDark ? "text-zinc-100" : "text-slate-900"}`}>{plan.name}</h3>
              </div>

              <ul className="space-y-4 mb-12 flex-1">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-4">
                    <div className={`mt-1 w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${
                      feature.included 
                        ? (isDark ? 'bg-white/10 text-white' : 'bg-blue-50 text-blue-600') 
                        : (isDark ? 'bg-zinc-900 text-zinc-800' : 'bg-slate-50 text-slate-300')
                    }`}>
                      {feature.included ? (
                        <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7" /></svg>
                      ) : (
                        <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M6 18L18 6M6 6l12 12" /></svg>
                      )}
                    </div>
                    <span className={`text-xs font-bold tracking-tight ${
                      feature.included 
                        ? (isDark ? 'text-zinc-300' : 'text-slate-700') 
                        : (isDark ? 'text-zinc-800 line-through' : 'text-slate-300 line-through')
                    }`}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="mt-auto pt-6">
                {isCurrent ? (
                  <div className={`w-full py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl ${isDark ? "bg-zinc-900 text-zinc-700" : "bg-slate-50 text-slate-400"}`}>
                    Active Plan
                  </div>
                ) : key === 'premium' || (key === 'starter' && currentPlan === 'free') ? (
                <button
                  onClick={() => handleUpgrade(key as any)}
                  disabled={upgrading}
                  className="btn-primary w-full py-4 uppercase tracking-[0.2em] text-[10px]"
                >
                  {upgrading ? 'Processing...' : `Subscribe to ${plan.name}`}
                  </button>
                  ) : (
                  <button
                  onClick={() => handleDowngradeTo(key as any)}
                  disabled={downgrading}
                  className="btn-secondary w-full py-4 uppercase tracking-[0.2em] text-[10px]"
                  >
                  {downgrading ? 'Processing...' : `Switch to ${plan.name}`}
                  </button>
                  )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
