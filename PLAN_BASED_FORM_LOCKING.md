# Plan-Based Form Locking Implementation

## Overview
This document describes the implementation of plan-based form locking that restricts certain features to paid plans (STARTER and PREMIUM) while locking them for FREE plan users.

## Architecture

### Backend Components

#### 1. Plan Enforcement Service (`backend/services/plan_enforcement.py`)
- Enforces plan limits based on subscription tier
- Checks feature availability (order forms, multi-AI support, etc.)
- Tracks usage limits (templates, rule messages, AI responses, products)

**Key Methods:**
- `can_use_order_form(user_id)` - Checks if user can use order form feature
- `can_add_template(user_id)` - Checks if user can add more templates
- `can_add_rule_message(user_id)` - Checks if user can add more rule messages
- `get_plan_limits(user_id)` - Returns all plan limits and current usage

#### 2. Subscription Router (`backend/routers/subscriptions.py`)
**New Endpoint:**
```
GET /api/subscriptions/plan-limits
```
Returns:
```json
{
  "plan_name": "free",
  "display_name": "Free",
  "limits": {
    "max_templates": 3,
    "max_rule_based_messages": 3,
    "max_ai_responses_per_session": 5,
    "max_products": 3,
    "website_fetch_scope": "homepage"
  },
  "features": {
    "order_form_enabled": false,
    "multi_ai_support": false,
    "setup_support": false,
    "team_collaboration": false,
    "analytics_dashboard": false,
    "crm_integrations": false,
    "managed_api": false
  },
  "usage": {
    "templates_used": 0,
    "rule_messages_used": 0,
    "ai_responses_used": 0,
    "products_fetched": 0
  }
}
```

### Frontend Components

#### 1. LockedFeature Component (`frontend/components/LockedFeature.tsx`)
A reusable component that wraps features and shows an upgrade prompt when locked.

**Props:**
- `isLocked: boolean` - Whether the feature is locked
- `children: ReactNode` - The feature content to wrap
- `featureName?: string` - Name of the locked feature
- `requiredPlan?: string` - Plan required to unlock (default: "STARTER or PREMIUM")
- `onUpgradeClick?: () => void` - Custom upgrade handler
- `className?: string` - Additional CSS classes
- `showOverlay?: boolean` - Whether to show the overlay (default: true)

**Usage Example:**
```tsx
<LockedFeature
  isLocked={!canUseOrderForm()}
  featureName="Order Form"
  requiredPlan="STARTER or PREMIUM"
>
  <input type="text" placeholder="Order form field..." />
</LockedFeature>
```

#### 2. LockedButton Component (`frontend/components/LockedFeature.tsx`)
A button variant that shows a lock icon and prompts upgrade when clicked if locked.

**Props:**
- `isLocked: boolean` - Whether the button is locked
- `onClick?: () => void` - Click handler (only fires if not locked)
- `children: ReactNode` - Button content
- `className?: string` - Additional CSS classes
- `disabled?: boolean` - Whether button is disabled
- `featureName?: string` - Name of the locked feature
- `requiredPlan?: string` - Plan required to unlock

**Usage Example:**
```tsx
<LockedButton
  isLocked={!canAddTemplate()}
  onClick={handleAddTemplate}
  featureName="Add Template"
  className="btn-primary"
>
  + Add Template
</LockedButton>
```

#### 3. usePlanLimits Hook (`frontend/hooks/usePlanLimits.ts`)
Custom React hook for checking plan limits and feature availability.

**Returns:**
```typescript
{
  planLimits: PlanLimits | null,
  loading: boolean,
  error: string | null,
  isFreePlan: boolean,
  isStarterPlan: boolean,
  isPremiumPlan: boolean,
  canAddTemplate: () => boolean,
  canAddRuleMessage: () => boolean,
  canUseOrderForm: () => boolean,
  canUseMultiAI: () => boolean,
  refetch: () => Promise<void>
}
```

**Usage Example:**
```tsx
const { canUseOrderForm, canAddTemplate, isFreePlan } = usePlanLimits();

// Check if feature is available
if (!canUseOrderForm()) {
  showToast("Order Form is locked on FREE plan", "error");
  return;
}
```

## Plan Tiers

### FREE Plan
- **Templates:** 3 max
- **Rule Messages:** 3 max
- **AI Responses:** 5 per session
- **Products:** 3 max
- **Website Fetch:** Homepage only
- **Order Form:** ❌ Locked
- **Multi-AI Support:** ❌ Locked (ChatGPT only)

### STARTER Plan ($29/month)
- **Templates:** 10 max
- **Rule Messages:** 10 max
- **AI Responses:** Unlimited
- **Products:** Unlimited
- **Website Fetch:** Homepage only
- **Order Form:** ✅ Unlocked
- **Multi-AI Support:** ✅ Unlocked (ChatGPT, Gemini, Claude)

### PREMIUM Plan ($99/month)
- **Templates:** Unlimited
- **Rule Messages:** Unlimited
- **AI Responses:** Unlimited
- **Products:** Unlimited
- **Website Fetch:** Full website
- **Order Form:** ✅ Unlocked
- **Multi-AI Support:** ✅ Unlocked
- **Managed API:** ✅ Included

## Implementation in Settings Page

The settings page (`frontend/app/dashboard/settings/page.tsx`) has been updated to:

1. **Import the locking components:**
```tsx
import { LockedFeature } from "@/components/LockedFeature";
import { usePlanLimits } from "@/hooks/usePlanLimits";
```

2. **Use the hook to check limits:**
```tsx
const { canUseOrderForm, canAddTemplate, canAddRuleMessage } = usePlanLimits();
```

3. **Wrap the order form section with LockedFeature:**
```tsx
<LockedFeature
  isLocked={!canUseOrderForm()}
  featureName="Order Form"
  requiredPlan="STARTER or PREMIUM"
>
  {/* Order form fields */}
</LockedFeature>
```

4. **Check limits before adding templates/rules:**
```tsx
const handleAddTemplate = () => {
  if (!canAddTemplate()) {
    showToast("Template limit reached. Upgrade to add more.", "error");
    return;
  }
  // Add template logic
};
```

## Upgrade Flow

When a user upgrades their plan:

1. User clicks "Upgrade Now" button in the locked feature overlay
2. Redirected to `/dashboard/subscription` page
3. User selects a paid plan (STARTER or PREMIUM)
4. Backend updates subscription via `/api/subscriptions/upgrade`
5. Frontend dispatches `plan-updated` event
6. `usePlanLimits` hook listens for this event and refetches limits
7. Locked features automatically unlock based on new plan

**Event Listener in Hook:**
```tsx
useEffect(() => {
  const handlePlanUpdate = () => {
    fetchPlanLimits();
  };
  
  window.addEventListener("plan-updated", handlePlanUpdate);
  return () => window.removeEventListener("plan-updated", handlePlanUpdate);
}, []);
```

**Event Dispatch After Upgrade:**
```tsx
// In subscription page after successful upgrade
window.dispatchEvent(new CustomEvent('plan-updated'));
```

## Testing Checklist

### FREE Plan User
- [ ] Order form section shows lock overlay
- [ ] Cannot edit order form fields
- [ ] Clicking "Add Template" shows limit error after 3 templates
- [ ] Clicking "Add Rule" shows limit error after 3 rules
- [ ] "Upgrade Now" button redirects to subscription page

### After Upgrading to STARTER
- [ ] Order form section unlocks automatically
- [ ] Can edit order form fields
- [ ] Can add up to 10 templates
- [ ] Can add up to 10 rule messages
- [ ] Multi-AI providers become available

### After Upgrading to PREMIUM
- [ ] All features unlocked
- [ ] No limits on templates
- [ ] No limits on rule messages
- [ ] Full website fetch available

## Database Schema

The plan limits are stored in the `plans` table:

```sql
CREATE TABLE plans (
  id INTEGER PRIMARY KEY,
  plan_name VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(50) NOT NULL,
  monthly_price FLOAT DEFAULT 0.0,
  
  -- Limits
  max_templates INTEGER DEFAULT 0,
  max_rule_based_messages INTEGER DEFAULT 0,
  max_ai_responses_per_session INTEGER DEFAULT 0,
  max_products INTEGER DEFAULT 0,
  website_fetch_scope VARCHAR(20) DEFAULT 'homepage',
  
  -- Features
  order_form_enabled BOOLEAN DEFAULT FALSE,
  multi_ai_support BOOLEAN DEFAULT FALSE,
  setup_support BOOLEAN DEFAULT FALSE,
  team_collaboration BOOLEAN DEFAULT FALSE,
  analytics_dashboard BOOLEAN DEFAULT FALSE,
  crm_integrations BOOLEAN DEFAULT FALSE,
  managed_api BOOLEAN DEFAULT FALSE,
  
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Future Enhancements

1. **Grace Period:** Allow users to keep using features for 7 days after downgrading
2. **Usage Warnings:** Show warnings when approaching limits (e.g., "2/3 templates used")
3. **Feature Tooltips:** Add tooltips explaining what each locked feature does
4. **Trial Period:** Offer 14-day trial of PREMIUM features for new users
5. **Progressive Disclosure:** Show locked features gradually as users explore
6. **A/B Testing:** Test different upgrade prompts and messaging

## Troubleshooting

### Issue: Locked features don't unlock after upgrade
**Solution:** Check that `plan-updated` event is being dispatched after upgrade:
```tsx
window.dispatchEvent(new CustomEvent('plan-updated'));
```

### Issue: Hook returns stale data
**Solution:** Call `refetch()` manually or ensure event listener is working:
```tsx
const { refetch } = usePlanLimits();
await refetch();
```

### Issue: Backend returns wrong plan limits
**Solution:** Verify subscription status in database:
```sql
SELECT u.email, s.status, p.plan_name, p.order_form_enabled
FROM users u
JOIN subscriptions s ON s.user_id = u.id
JOIN plans p ON p.id = s.plan_id
WHERE u.email = 'user@example.com';
```

## Security Considerations

1. **Backend Validation:** Always validate plan limits on the backend, not just frontend
2. **API Authorization:** Ensure `/api/subscriptions/plan-limits` requires authentication
3. **Rate Limiting:** Implement rate limiting on upgrade endpoints to prevent abuse
4. **Audit Logging:** Log all plan changes and feature access attempts

## Performance Optimization

1. **Caching:** Plan limits are cached in React state and only refetched on plan updates
2. **Lazy Loading:** LockedFeature component only renders overlay when locked
3. **Event-Driven:** Uses browser events instead of polling for plan updates
4. **Memoization:** Consider memoizing `canUse*` functions if performance issues arise

## Conclusion

This implementation provides a robust, user-friendly plan-based locking system that:
- Clearly communicates feature restrictions to FREE users
- Provides seamless upgrade path
- Automatically unlocks features after upgrade
- Maintains good UX with visual feedback
- Scales to support additional features and plans
