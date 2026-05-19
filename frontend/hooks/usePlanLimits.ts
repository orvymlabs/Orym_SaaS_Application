/**
 * Custom hook for plan-based feature locking
 * Checks user's subscription plan and enforces limits
 */
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export interface PlanLimits {
  plan_name: string;
  display_name: string;
  limits: {
    max_templates: number;
    max_rule_based_messages: number;
    max_ai_responses_per_session: number;
    max_products: number;
    website_fetch_scope: string;
  };
  features: {
    order_form_enabled: boolean;
    multi_ai_support: boolean;
    setup_support: boolean;
    team_collaboration: boolean;
    analytics_dashboard: boolean;
    crm_integrations: boolean;
    managed_api: boolean;
  };
  usage: {
    templates_used: number;
    rule_messages_used: number;
    ai_responses_used: number;
    products_fetched: number;
  };
}

export function usePlanLimits() {
  const [planLimits, setPlanLimits] = useState<PlanLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlanLimits = async () => {
    try {
      setLoading(true);
      const data = await apiGet<PlanLimits>("/api/subscriptions/plan-limits");
      setPlanLimits(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch plan limits");
      console.error("Error fetching plan limits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlanLimits();

    // Listen for plan updates
    const handlePlanUpdate = () => {
      fetchPlanLimits();
    };

    window.addEventListener("plan-updated", handlePlanUpdate);
    return () => window.removeEventListener("plan-updated", handlePlanUpdate);
  }, []);

  const isFreePlan = planLimits?.plan_name === "free";
  const isStarterPlan = planLimits?.plan_name === "starter";
  const isPremiumPlan = planLimits?.plan_name === "premium";

  const canAddTemplate = () => {
    if (!planLimits) return false;
    const limit = planLimits.limits.max_templates;
    if (limit === 0) return true; // Unlimited
    return planLimits.usage.templates_used < limit;
  };

  const canAddRuleMessage = () => {
    if (!planLimits) return false;
    const limit = planLimits.limits.max_rule_based_messages;
    if (limit === 0) return true; // Unlimited
    return planLimits.usage.rule_messages_used < limit;
  };

  const canUseOrderForm = () => {
    return planLimits?.features.order_form_enabled || false;
  };

  const canUseMultiAI = () => {
    return planLimits?.features.multi_ai_support || false;
  };

  return {
    planLimits,
    loading,
    error,
    isFreePlan,
    isStarterPlan,
    isPremiumPlan,
    canAddTemplate,
    canAddRuleMessage,
    canUseOrderForm,
    canUseMultiAI,
    refetch: fetchPlanLimits,
  };
}
