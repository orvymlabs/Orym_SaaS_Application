# Quick Start Guide - Plan-Based Form Locking

## Installation Complete ✅

The plan-based form locking system has been successfully implemented in your application.

## What You Can Do Now

### 1. Test the Locking System

**As a FREE user:**
```bash
# Login with a FREE plan account
# Navigate to: /dashboard/settings
# Scroll to "Form Submission" section
# You should see a lock overlay with upgrade prompt
```

**Upgrade Flow:**
```bash
# Click "Upgrade Now" button
# Select STARTER or PREMIUM plan
# Complete upgrade
# Return to settings - form should now be unlocked
```

### 2. Use in Your Components

**Import the components:**
```tsx
import { LockedFeature } from "@/components/LockedFeature";
import { usePlanLimits } from "@/hooks/usePlanLimits";
```

**Lock a feature:**
```tsx
const { canUseOrderForm } = usePlanLimits();

<LockedFeature
  isLocked={!canUseOrderForm()}
  featureName="Order Form"
  requiredPlan="STARTER or PREMIUM"
>
  {/* Your feature content */}
</LockedFeature>
```

### 3. Check Plan Limits

```tsx
const { 
  canAddTemplate, 
  canAddRuleMessage, 
  canUseOrderForm,
  isFreePlan,
  planLimits 
} = usePlanLimits();

// Check before adding
if (!canAddTemplate()) {
  alert("Template limit reached!");
  return;
}
```

## Files Created

✅ `frontend/components/LockedFeature.tsx` - Locking UI component  
✅ `frontend/hooks/usePlanLimits.ts` - Plan limits hook  
✅ `frontend/examples/PlanLockingExamples.tsx` - Usage examples  
✅ `backend/routers/subscriptions.py` - Updated with plan-limits endpoint  
✅ `PLAN_BASED_FORM_LOCKING.md` - Full documentation  
✅ `IMPLEMENTATION_SUMMARY.md` - Implementation summary  

## Files Modified

✅ `frontend/app/dashboard/settings/page.tsx` - Integrated locking system  
✅ `frontend/components/ui/index.ts` - Export updates  

## API Endpoints

```
GET  /api/subscriptions/plan-limits    - Get current plan limits
POST /api/subscriptions/upgrade         - Upgrade to paid plan
GET  /api/subscriptions/current         - Get current subscription
```

## Plan Features

| Feature | FREE | STARTER | PREMIUM |
|---------|------|---------|---------|
| Order Form | ❌ | ✅ | ✅ |
| Templates | 3 | 10 | ∞ |
| Rules | 3 | 10 | ∞ |
| AI Responses | 5/session | ∞ | ∞ |
| Multi-AI | ❌ | ✅ | ✅ |

## Testing Checklist

- [ ] Login as FREE user
- [ ] Verify order form is locked in settings
- [ ] Click "Upgrade Now" button
- [ ] Upgrade to STARTER plan
- [ ] Verify order form unlocks automatically
- [ ] Try adding templates (should allow up to 10)
- [ ] Try adding rules (should allow up to 10)

## Next Steps

1. **Test the implementation:**
   - Test with FREE plan account
   - Test upgrade flow
   - Test downgrade flow

2. **Lock additional features (optional):**
   - Lock multi-AI providers for FREE users
   - Lock analytics dashboard for non-PREMIUM users
   - Lock team collaboration features

3. **Add usage indicators (optional):**
   - Show "2/3 templates used" badges
   - Add progress bars for limits
   - Warning when approaching limit

4. **Deploy:**
   - Deploy backend changes
   - Deploy frontend changes
   - Test in production

## Support

For detailed documentation, see:
- `PLAN_BASED_FORM_LOCKING.md` - Complete technical documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `frontend/examples/PlanLockingExamples.tsx` - Code examples

## Troubleshooting

**Issue: Features don't unlock after upgrade**
```tsx
// Manually trigger refetch
const { refetch } = usePlanLimits();
await refetch();
```

**Issue: Hook returns null**
```tsx
// Check loading state
const { planLimits, loading, error } = usePlanLimits();
if (loading) return <div>Loading...</div>;
if (error) return <div>Error: {error}</div>;
```

## Success! 🎉

Your plan-based form locking system is ready to use. FREE users will see locked features with upgrade prompts, and features will automatically unlock when they upgrade to paid plans.
