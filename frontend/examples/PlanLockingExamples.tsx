/**
 * Usage Examples for Plan-Based Form Locking
 *
 * This file demonstrates how to use the LockedFeature component
 * and usePlanLimits hook throughout the application.
 */

import { LockedFeature, LockedButton } from "@/components/LockedFeature";
import { usePlanLimits } from "@/hooks/usePlanLimits";

// ============================================
// Example 1: Locking an entire section
// ============================================
export function OrderFormExample() {
  const { canUseOrderForm } = usePlanLimits();

  return (
    <LockedFeature
      isLocked={!canUseOrderForm()}
      featureName="Order Form"
      requiredPlan="STARTER or PREMIUM"
    >
      <div className="order-form">
        <input type="text" placeholder="Customer Name" />
        <input type="text" placeholder="Product" />
        <button>Submit Order</button>
      </div>
    </LockedFeature>
  );
}

// ============================================
// Example 2: Locking a button
// ============================================
export function AddTemplateButtonExample() {
  const { canAddTemplate } = usePlanLimits();

  const handleAddTemplate = () => {
    console.log("Adding template...");
  };

  return (
    <LockedButton
      isLocked={!canAddTemplate()}
      onClick={handleAddTemplate}
      featureName="Add Template"
      requiredPlan="STARTER or PREMIUM"
      className="btn-primary"
    >
      + Add Template
    </LockedButton>
  );
}

// ============================================
// Example 3: Conditional rendering based on plan
// ============================================
export function ConditionalFeatureExample() {
  const { isFreePlan, isPremiumPlan, planLimits } = usePlanLimits();

  return (
    <div>
      {isFreePlan && (
        <div className="upgrade-banner">
          <p>You're on the FREE plan. Upgrade to unlock more features!</p>
        </div>
      )}

      {isPremiumPlan && (
        <div className="premium-badge">
          <p>⭐ Premium Member</p>
        </div>
      )}

      <p>Templates: {planLimits?.usage.templates_used} / {planLimits?.limits.max_templates || "∞"}</p>
    </div>
  );
}

// ============================================
// Example 4: Checking limits before action
// ============================================
export function CheckLimitsExample() {
  const { canAddTemplate, canAddRuleMessage, planLimits } = usePlanLimits();

  const handleAddTemplate = () => {
    if (!canAddTemplate()) {
      alert(`Template limit reached! Your ${planLimits?.display_name} plan allows ${planLimits?.limits.max_templates} templates.`);
      return;
    }

    // Proceed with adding template
    console.log("Adding template...");
  };

  const handleAddRule = () => {
    if (!canAddRuleMessage()) {
      alert(`Rule limit reached! Your ${planLimits?.display_name} plan allows ${planLimits?.limits.max_rule_based_messages} rules.`);
      return;
    }

    // Proceed with adding rule
    console.log("Adding rule...");
  };

  return (
    <div>
      <button onClick={handleAddTemplate}>Add Template</button>
      <button onClick={handleAddRule}>Add Rule</button>
    </div>
  );
}

// ============================================
// Example 5: Custom upgrade handler
// ============================================
export function CustomUpgradeExample() {
  const { canUseOrderForm } = usePlanLimits();

  const handleCustomUpgrade = () => {
    // Custom logic before redirecting
    console.log("User wants to upgrade!");

    // Track analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'upgrade_intent', {
        feature: 'order_form',
        source: 'settings_page'
      });
    }

    // Redirect to subscription page
    window.location.href = '/dashboard/subscription';
  };

  return (
    <LockedFeature
      isLocked={!canUseOrderForm()}
      featureName="Order Form"
      requiredPlan="STARTER or PREMIUM"
      onUpgradeClick={handleCustomUpgrade}
    >
      <div className="order-form">
        {/* Form content */}
      </div>
    </LockedFeature>
  );
}

// ============================================
// Example 6: Locking with custom styling
// ============================================
export function CustomStyledLockExample() {
  const { canUseOrderForm } = usePlanLimits();

  return (
    <LockedFeature
      isLocked={!canUseOrderForm()}
      featureName="Advanced Analytics"
      requiredPlan="PREMIUM"
      className="my-custom-class"
      showOverlay={true}
    >
      <div className="analytics-dashboard">
        <h2>Analytics Dashboard</h2>
        <div className="charts">
          {/* Chart components */}
        </div>
      </div>
    </LockedFeature>
  );
}

// ============================================
// Example 7: Loading and error states
// ============================================
export function LoadingStateExample() {
  const { planLimits, loading, error } = usePlanLimits();

  if (loading) {
    return <div>Loading plan information...</div>;
  }

  if (error) {
    return <div>Error loading plan: {error}</div>;
  }

  if (!planLimits) {
    return <div>No plan information available</div>;
  }

  return (
    <div>
      <h3>Your Plan: {planLimits.display_name}</h3>
      <ul>
        <li>Templates: {planLimits.limits.max_templates || "Unlimited"}</li>
        <li>Rules: {planLimits.limits.max_rule_based_messages || "Unlimited"}</li>
        <li>Order Form: {planLimits.features.order_form_enabled ? "✅" : "❌"}</li>
      </ul>
    </div>
  );
}

// ============================================
// Example 8: Manual refetch after action
// ============================================
export function ManualRefetchExample() {
  const { refetch, planLimits } = usePlanLimits();

  const handleUpgradeComplete = async () => {
    // After successful upgrade, manually refetch limits
    await refetch();
    console.log("Plan limits refreshed!");
  };

  return (
    <div>
      <p>Current Plan: {planLimits?.display_name}</p>
      <button onClick={handleUpgradeComplete}>
        Refresh Plan Info
      </button>
    </div>
  );
}

// ============================================
// Example 9: Locking multiple features
// ============================================
export function MultipleLockedFeaturesExample() {
  const { canUseOrderForm, canUseMultiAI, isPremiumPlan } = usePlanLimits();

  return (
    <div className="features-grid">
      <LockedFeature
        isLocked={!canUseOrderForm()}
        featureName="Order Form"
        requiredPlan="STARTER or PREMIUM"
      >
        <div className="feature-card">Order Form Feature</div>
      </LockedFeature>

      <LockedFeature
        isLocked={!canUseMultiAI()}
        featureName="Multi-AI Support"
        requiredPlan="STARTER or PREMIUM"
      >
        <div className="feature-card">Multi-AI Providers</div>
      </LockedFeature>

      <LockedFeature
        isLocked={!isPremiumPlan}
        featureName="Analytics Dashboard"
        requiredPlan="PREMIUM"
      >
        <div className="feature-card">Advanced Analytics</div>
      </LockedFeature>
    </div>
  );
}

// ============================================
// Example 10: Inline lock without overlay
// ============================================
export function InlineLockExample() {
  const { canUseOrderForm } = usePlanLimits();

  return (
    <div>
      <h3>Order Form Settings</h3>

      {!canUseOrderForm() ? (
        <div className="inline-upgrade-prompt">
          <p>🔒 Order Form is locked on FREE plan</p>
          <a href="/dashboard/subscription" className="btn-primary">
            Upgrade to STARTER
          </a>
        </div>
      ) : (
        <div className="order-form-settings">
          <input type="text" placeholder="Form template..." />
          <button>Save Settings</button>
        </div>
      )}
    </div>
  );
}
