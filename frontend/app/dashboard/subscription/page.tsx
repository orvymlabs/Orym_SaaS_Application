"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useToast } from "@/components/ui";
import { useTheme } from "@/lib/useTheme";

interface Plan {
  id: number;
  plan_name: string;
  display_name: string;
  monthly_price: number;
  yearly_price: number | null;
  max_templates: number;
  max_rule_based_messages: number;
  max_ai_responses_per_session: number;
  max_products: number;
  website_fetch_scope: string;
  order_form_enabled: boolean;
  multi_ai_support: boolean;
  setup_support: boolean;
  team_collaboration: boolean;
  analytics_dashboard: boolean;
  crm_integrations: boolean;
  managed_api: boolean;
}

interface Subscription {
  id: number;
  plan: Plan;
  status: string;
  billing_cycle: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  usage: {
    templates_used: number;
    rule_messages_used: number;
    ai_responses_used: number;
    products_fetched: number;
  };
}

interface UsageStats {
  templates_used: number;
  templates_limit: number;
  rule_messages_used: number;
  rule_messages_limit: number;
  ai_responses_used: number;
  ai_responses_limit: number;
  products_fetched: number;
  products_limit: number;
}

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  const { showToast, ToastContainer } = useToast();
  const { isDark } = useTheme();

  useEffect(() => {
    loadSubscriptionData();

    // Check for success/cancel query params
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      showToast("Payment successful! Your subscription is now active.", "success");
      // Clean URL
      window.history.replaceState({}, '', '/dashboard/subscription');
    } else if (params.get('canceled') === 'true') {
      showToast("Payment canceled. You can try again anytime.", "info");
      // Clean URL
      window.history.replaceState({}, '', '/dashboard/subscription');
    }
  }, []);

  const loadSubscriptionData = async () => {
    try {
      const [subData, plansData, usageData] = await Promise.all([
        apiGet<Subscription>("/api/subscriptions/current"),
        apiGet<Plan[]>("/api/subscriptions/plans"),
        apiGet<UsageStats>("/api/subscriptions/usage"),
      ]);
      setSubscription(subData);
      setPlans(plansData);
      setUsage(usageData);
    } catch (error) {
      showToast("Failed to load subscription data", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planName: string, monthlyPrice: number) => {
    if (!confirm(`Switch to ${planName.toUpperCase()} plan?`)) return;

    setUpgrading(true);
    try {
      await apiPost("/api/subscriptions/upgrade", {
        plan_name: planName,
        billing_cycle: "monthly",
      });
      showToast(`Successfully switched to ${planName.toUpperCase()}!`, "success");
      
      // Notify layout to update plan badge without refresh
      window.dispatchEvent(new CustomEvent('plan-updated'));
      
      await loadSubscriptionData();
    } catch (error: any) {
      showToast(error?.message || "Failed to switch plan", "error");
    } finally {
      setUpgrading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Cancel your subscription? You'll retain access until the end of your billing period.")) return;

    try {
      await apiPost("/api/subscriptions/cancel", {});
      showToast("Subscription will be canceled at period end", "success");
      await loadSubscriptionData();
    } catch (error) {
      showToast("Cancellation failed", "error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className={`w-16 h-16 border-4 rounded-full animate-spin mx-auto mb-4 ${isDark ? "border-zinc-800" : "border-slate-100"}`} style={{ borderTopColor: isDark ? 'white' : 'black' }}></div>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-400"} font-black uppercase tracking-[0.2em] text-[10px]`}>Loading Subscription...</p>
        </div>
      </div>
    );
  }

  const currentPlanName = subscription?.plan.plan_name || "free";

  const formatLimit = (limit: number) => {
    return limit === 0 ? "Unlimited" : limit.toString();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-12 pb-24 animate-in fade-in duration-500">
      <ToastContainer />

      {/* Header */}
      <div className="text-center max-w-2xl mx-auto">
        <h1 className={`text-5xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>
          Subscription & Usage
        </h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-medium mt-4`}>
          Manage your plan and track your usage limits
        </p>
      </div>

      {/* Current Usage Stats */}
      {usage && subscription && (
        <div className={`rounded-[3rem] border shadow-2xl p-10 max-w-5xl mx-auto ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-slate-100"}`}>
          <div className="mb-8">
            <h2 className={`text-2xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
              Current Plan: {subscription.plan.display_name}
            </h2>
            <p className={`text-sm ${isDark ? "text-zinc-500" : "text-slate-500"} mt-1`}>
              {subscription.plan.monthly_price > 0 ? `$${subscription.plan.monthly_price}/month` : "Free Forever"}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Templates */}
            <div className="space-y-3">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                Chat Templates
              </p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                {usage.templates_used} <span className="text-zinc-700 text-xl">/</span> {formatLimit(usage.templates_limit)}
              </p>
              {usage.templates_limit > 0 && (
                <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                  <div
                    className={`h-full transition-all duration-1000 ${isDark ? "bg-white" : "bg-[#C9A84C]"}`}
                    style={{ width: `${Math.min((usage.templates_used / usage.templates_limit) * 100, 100)}%` }}
                  ></div>
                </div>
              )}
            </div>

            {/* Rule Messages */}
            <div className="space-y-3">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                Rule Messages
              </p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                {usage.rule_messages_used} <span className="text-zinc-700 text-xl">/</span> {formatLimit(usage.rule_messages_limit)}
              </p>
              {usage.rule_messages_limit > 0 && (
                <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                  <div
                    className={`h-full transition-all duration-1000 ${isDark ? "bg-zinc-400" : "bg-[#00C9A7]"}`}
                    style={{ width: `${Math.min((usage.rule_messages_used / usage.rule_messages_limit) * 100, 100)}%` }}
                  ></div>
                </div>
              )}
            </div>

            {/* AI Responses */}
            <div className="space-y-3">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                AI Responses
              </p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                {usage.ai_responses_used} <span className="text-zinc-700 text-xl">/</span> {formatLimit(usage.ai_responses_limit)}
              </p>
              {usage.ai_responses_limit > 0 && (
                <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                  <div
                    className={`h-full transition-all duration-1000 ${isDark ? "bg-white" : "bg-purple-500"}`}
                    style={{ width: `${Math.min((usage.ai_responses_used / usage.ai_responses_limit) * 100, 100)}%` }}
                  ></div>
                </div>
              )}
            </div>

            {/* Products */}
            <div className="space-y-3">
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                Products Fetched
              </p>
              <p className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                {usage.products_fetched} <span className="text-zinc-700 text-xl">/</span> {formatLimit(usage.products_limit)}
              </p>
              {usage.products_limit > 0 && (
                <div className={`h-1.5 rounded-full overflow-hidden ${isDark ? "bg-white/5" : "bg-slate-100"}`}>
                  <div
                    className={`h-full transition-all duration-1000 ${isDark ? "bg-zinc-400" : "bg-emerald-500"}`}
                    style={{ width: `${Math.min((usage.products_fetched / usage.products_limit) * 100, 100)}%` }}
                  ></div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Available Plans */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.sort((a, b) => {
          // Order: free (left), starter (middle), premium (right)
          const order = { free: 1, starter: 2, premium: 3 };
          return (order[a.plan_name as keyof typeof order] || 99) - (order[b.plan_name as keyof typeof order] || 99);
        }).map((plan) => {
          const isCurrent = plan.plan_name === currentPlanName;
          const isPopular = plan.plan_name === "starter";
          const isPremium = plan.plan_name === "premium";

          return (
            <div
              key={plan.id}
              className={`rounded-[3rem] p-10 border-2 transition-all duration-500 relative flex flex-col ${
                isPopular && !isCurrent
                  ? isDark ? 'bg-[#0F0F0F] border-[#C9A84C]/50 shadow-2xl shadow-yellow-900/20' : 'bg-white border-[#C9A84C] shadow-2xl shadow-yellow-100'
                  : isPremium && !isCurrent
                  ? isDark ? 'bg-[#0F0F0F] border-[#00C9A7]/50 shadow-2xl shadow-teal-900/20' : 'bg-white border-[#00C9A7] shadow-2xl shadow-teal-100'
                  : isDark
                  ? isCurrent ? 'bg-[#0F0F0F] border-white/20 shadow-2xl shadow-black' : 'bg-[#090909] border-zinc-800 hover:border-zinc-700'
                  : isCurrent ? 'bg-white border-slate-500 shadow-2xl shadow-slate-50' : 'bg-white border-slate-100 hover:border-slate-200'
              }`}
            >
              {isPopular && !isCurrent && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#C9A84C] to-[#E8C97A] text-black px-6 py-2 text-[10px] font-black uppercase tracking-widest rounded-full shadow-xl">
                  ⭐ Most Popular
                </div>
              )}
              {isCurrent && (
                <div className={`absolute top-6 right-8 px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${isDark ? "bg-white text-black" : "bg-[#C9A84C] text-black"}`}>
                  Current Plan
                </div>
              )}

              <div className="mb-8">
                <h2 className={`text-3xl font-black uppercase tracking-tight mb-2 ${
                  isPremium ? "text-[#00C9A7]" : isPopular ? "text-[#E8C97A]" : isDark ? "text-white" : "text-slate-900"
                }`}>
                  {plan.display_name}
                </h2>
                <div className="flex items-baseline gap-1">
                  {plan.monthly_price > 0 ? (
                    <>
                      <span className={`text-4xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                        ${plan.monthly_price}
                      </span>
                      <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                        /month
                      </span>
                    </>
                  ) : isPremium ? (
                    <span className={`text-2xl font-black ${isDark ? "text-[#00C9A7]" : "text-[#00C9A7]"}`}>
                      Contact Sales
                    </span>
                  ) : (
                    <span className={`text-4xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                      Free
                    </span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-8 flex-1 text-sm">
                <li className={`flex items-start gap-3 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>{formatLimit(plan.max_templates)}</strong> Chat Templates</span>
                </li>
                <li className={`flex items-start gap-3 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>{formatLimit(plan.max_rule_based_messages)}</strong> Rule Messages</span>
                </li>
                <li className={`flex items-start gap-3 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>{formatLimit(plan.max_ai_responses_per_session)}</strong> AI Responses/Session</span>
                </li>
                <li className={`flex items-start gap-3 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>{formatLimit(plan.max_products)}</strong> Products</span>
                </li>
                <li className={`flex items-start gap-3 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>{plan.website_fetch_scope === "full" ? "Full Website" : "Homepage Only"}</strong> Fetch</span>
                </li>
                <li className={`flex items-start gap-3 ${plan.order_form_enabled ? (isDark ? "text-zinc-300" : "text-slate-700") : (isDark ? "text-zinc-700" : "text-slate-400")}`}>
                  <span className={plan.order_form_enabled ? "text-green-500 mt-0.5" : "text-red-500 mt-0.5"}>
                    {plan.order_form_enabled ? "✓" : "✗"}
                  </span>
                  <span>Order Form</span>
                </li>
                <li className={`flex items-start gap-3 ${plan.multi_ai_support ? (isDark ? "text-zinc-300" : "text-slate-700") : (isDark ? "text-zinc-700" : "text-slate-400")}`}>
                  <span className={plan.multi_ai_support ? "text-green-500 mt-0.5" : "text-red-500 mt-0.5"}>
                    {plan.multi_ai_support ? "✓" : "✗"}
                  </span>
                  <span>Multi-AI Support</span>
                </li>
                {plan.managed_api && (
                  <li className={`flex items-start gap-3 ${isDark ? "text-[#00C9A7]" : "text-[#00C9A7]"} font-bold`}>
                    <span className="mt-0.5">⭐</span>
                    <span>Managed API Included</span>
                  </li>
                )}
              </ul>

              <div className="mt-auto pt-6">
                {isCurrent ? (
                  <div className="space-y-3">
                    <div className={`w-full py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl ${isDark ? "bg-zinc-900 text-zinc-700" : "bg-slate-50 text-slate-400"}`}>
                      Active Plan
                    </div>
                    {plan.monthly_price > 0 && subscription?.cancel_at_period_end === false && (
                      <button
                        onClick={handleCancel}
                        className={`w-full py-3 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl border ${isDark ? "border-zinc-800 text-zinc-500 hover:border-zinc-700" : "border-slate-200 text-slate-500 hover:border-slate-300"}`}
                      >
                        Cancel Subscription
                      </button>
                    )}
                  </div>
                ) : plan.monthly_price === 0 && !isPremium ? (
                  <button
                    onClick={() => handleUpgrade(plan.plan_name, plan.monthly_price)}
                    disabled={upgrading}
                    className={`w-full py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl border ${isDark ? "border-zinc-700 text-zinc-400 hover:bg-zinc-900" : "border-slate-300 text-slate-600 hover:bg-slate-50"}`}
                  >
                    {upgrading ? "Processing..." : `Switch to ${plan.display_name}`}
                  </button>
                ) : isPremium ? (
                  <button
                    onClick={() => handleUpgrade(plan.plan_name, plan.monthly_price)}
                    disabled={upgrading}
                    className={`w-full py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl ${isDark ? "bg-[#00C9A7] text-black hover:bg-[#00E5C0]" : "bg-[#00C9A7] text-white hover:bg-[#00E5C0]"}`}
                  >
                    {upgrading ? "Processing..." : `Switch to ${plan.display_name}`}
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(plan.plan_name, plan.monthly_price)}
                    disabled={upgrading}
                    className={`w-full py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl ${
                      isPopular
                        ? "bg-gradient-to-r from-[#C9A84C] to-[#E8C97A] text-black hover:shadow-xl"
                        : isDark ? "bg-white text-black hover:bg-zinc-100" : "bg-slate-900 text-white hover:bg-slate-800"
                    }`}
                  >
                    {upgrading ? "Redirecting to checkout..." : `Upgrade to ${plan.display_name}`}
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
