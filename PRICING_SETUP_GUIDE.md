# Pricing & Subscription System - Setup Guide

## Overview

Complete pricing and subscription management system with Stripe integration, plan enforcement, and usage tracking based on CLAUDE.md specifications.

## Features Implemented

### 1. **Three-Tier Pricing Plans**
- **FREE**: 3 templates, 3 rule messages, 5 AI responses/session, 3 products, homepage only
- **STARTER ($9.99/month)**: 10 templates, 10 rule messages, unlimited AI, unlimited products, homepage only
- **PREMIUM (Contact Sales)**: Unlimited everything, full website fetch, managed API

### 2. **Database Schema**
- `plans` table with all plan features and limits
- `subscriptions` table tracking user subscriptions and usage
- Stripe integration fields (customer_id, subscription_id, price_id)

### 3. **Plan Enforcement Service**
- Real-time limit checking for templates, messages, AI responses, products
- Feature gating (order form, multi-AI support, website fetch scope)
- Usage tracking and monthly reset

### 4. **Stripe Payment Integration**
- Secure checkout sessions for paid plans
- Webhook handling for subscription lifecycle
- Automatic plan upgrades/downgrades
- Subscription cancellation

### 5. **API Endpoints**
- `GET /api/subscriptions/plans` - List available plans
- `GET /api/subscriptions/current` - Get user's subscription
- `GET /api/subscriptions/usage` - Get usage statistics
- `POST /api/subscriptions/upgrade` - Upgrade to free plan
- `POST /api/subscriptions/create-checkout` - Create Stripe checkout
- `POST /api/subscriptions/cancel` - Cancel subscription
- `POST /api/subscriptions/webhook` - Stripe webhook handler

### 6. **Frontend UI**
- Modern pricing page at `/pricing`
- Subscription management dashboard at `/dashboard/subscription`
- Usage tracking with progress bars
- Stripe checkout integration

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Backend
cd backend
pip install stripe

# Frontend (already has required packages)
cd frontend
npm install
```

### Step 2: Configure Environment Variables

Add to `backend/.env`:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Get these from: https://dashboard.stripe.com/test/apikeys
```

### Step 3: Run Database Migration

```bash
cd backend
python migrate_subscriptions.py
```

This will:
- Add new columns to existing tables
- Create subscriptions table
- Seed FREE, STARTER, and PREMIUM plans
- Create default subscriptions for existing users

### Step 4: Configure Stripe Webhook (Production)

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/api/subscriptions/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copy webhook signing secret to `.env`

### Step 5: Test the System

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3000/pricing`
4. Test plan upgrades and checkout flow

---

## Usage Examples

### Checking Plan Limits in Code

```python
from services.plan_enforcement import PlanEnforcementService

# In your endpoint
enforcement = PlanEnforcementService(db)

# Check if user can add template
can_add, message = enforcement.can_add_template(user_id)
if not can_add:
    raise HTTPException(400, detail=message)

# Check if user can use AI
can_use, message = enforcement.can_use_ai_response(user_id, phone_number)
if not can_use:
    raise HTTPException(400, detail=message)

# Increment usage
enforcement.increment_ai_usage(user_id)
```

### Frontend Checkout Flow

```typescript
// User clicks "Upgrade to STARTER"
const response = await apiPost("/api/subscriptions/create-checkout", {
  plan_name: "starter",
  success_url: `${window.location.origin}/dashboard/subscription?success=true`,
  cancel_url: `${window.location.origin}/dashboard/subscription?canceled=true`,
});

// Redirect to Stripe
window.location.href = response.checkout_url;
```

---

## Plan Limits Reference

| Feature | FREE | STARTER | PREMIUM |
|---------|------|---------|---------|
| Chat Templates | 3 | 10 | Unlimited |
| Rule Messages | 3 | 10 | Unlimited |
| AI Responses/Session | 5 | Unlimited | Unlimited |
| Products | 3 | Unlimited | Unlimited |
| Website Fetch | Homepage | Homepage | Full Site |
| Order Form | ❌ | ✅ | ✅ |
| Multi-AI (Gemini, Claude) | ❌ | ✅ | ✅ |
| Setup Support | ❌ | ✅ | ✅ |
| Managed API | ❌ | ❌ | ✅ |
| Price | Free | $9.99/mo | Contact Sales |

---

## Webhook Testing (Development)

Use Stripe CLI for local webhook testing:

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Forward webhooks to local server
stripe listen --forward-to localhost:8001/api/subscriptions/webhook

# Test checkout completion
stripe trigger checkout.session.completed
```

---

## Security Notes

1. **Never expose Stripe secret keys** in frontend code
2. **Always verify webhook signatures** in production
3. **Use HTTPS** for webhook endpoints
4. **Validate plan limits** on backend, not just frontend
5. **Encrypt sensitive data** (API keys, tokens)

---

## Troubleshooting

### Migration fails with "column already exists"
- The migration script handles this automatically
- Safe to re-run multiple times

### Stripe checkout not working
- Check `STRIPE_SECRET_KEY` is set correctly
- Verify Stripe account is activated
- Check browser console for errors

### Webhook not receiving events
- Verify webhook URL is publicly accessible
- Check webhook signing secret matches
- Review Stripe Dashboard → Webhooks → Events

### Plan limits not enforcing
- Ensure migration ran successfully
- Check subscription status is "active"
- Verify plan_enforcement service is imported

---

## Next Steps

1. **Add Stripe to production**: Update `.env` with live keys
2. **Configure webhook endpoint**: Set up production webhook URL
3. **Test payment flow**: Complete test purchase with Stripe test cards
4. **Monitor usage**: Track plan limits and usage patterns
5. **Add analytics**: Monitor conversion rates and upgrades

---

## Support

For issues or questions:
- Check logs: `backend/logs/` or console output
- Review Stripe Dashboard for payment issues
- Test with Stripe test cards: https://stripe.com/docs/testing

---

## Files Modified/Created

### Backend
- `backend/models/__init__.py` - Added Subscription model, updated Plan and User
- `backend/database.py` - Added Subscription to imports
- `backend/services/plan_enforcement.py` - Plan limit enforcement
- `backend/services/stripe_service.py` - Stripe integration
- `backend/routers/subscriptions.py` - Subscription API endpoints
- `backend/migrate_subscriptions.py` - Database migration script
- `backend/config.py` - Added Stripe configuration
- `backend/main.py` - Registered subscription router

### Frontend
- `frontend/app/pricing/page.tsx` - Public pricing page
- `frontend/app/pricing/pricing.css` - Pricing page styles
- `frontend/app/dashboard/subscription/page.tsx` - Subscription management

### Root
- `orvym-nexus-pricing.html` - Standalone pricing page (updated)
