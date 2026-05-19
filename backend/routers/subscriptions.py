"""
Subscription Management API

Endpoints for:
- Viewing available plans
- Getting current subscription
- Creating Stripe checkout sessions
- Upgrading/downgrading plans
- Canceling subscriptions
- Viewing usage stats
- Handling Stripe webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, Plan, Subscription
from routers.auth import get_current_user  # Fixed import
from services.plan_enforcement import PlanEnforcementService
from services.stripe_service import StripeService
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


# Schemas
class PlanResponse(BaseModel):
    id: int
    plan_name: str
    display_name: str
    monthly_price: float
    yearly_price: Optional[float]
    max_templates: int
    max_rule_based_messages: int
    max_ai_responses_per_session: int
    max_products: int
    website_fetch_scope: str
    order_form_enabled: bool
    multi_ai_support: bool
    setup_support: bool
    team_collaboration: bool
    analytics_dashboard: bool
    crm_integrations: bool
    managed_api: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    plan: PlanResponse
    status: str
    billing_cycle: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    trial_end: Optional[datetime]
    usage: Dict[str, int]

    class Config:
        from_attributes = True


class UpgradeRequest(BaseModel):
    plan_name: str
    billing_cycle: str = "monthly"  # monthly or yearly


class CheckoutRequest(BaseModel):
    plan_name: str
    success_url: str
    cancel_url: str


class UsageResponse(BaseModel):
    templates_used: int
    templates_limit: int
    rule_messages_used: int
    rule_messages_limit: int
    ai_responses_used: int
    ai_responses_limit: int
    products_fetched: int
    products_limit: int


@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available subscription plans"""
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.monthly_price).all()
    return plans


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's current subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    # Build response with usage data
    response_data = {
        "id": subscription.id,
        "plan": subscription.plan,
        "status": subscription.status,
        "billing_cycle": subscription.billing_cycle,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "trial_end": subscription.trial_end,
        "usage": {
            "templates_used": subscription.templates_used,
            "rule_messages_used": subscription.rule_messages_used,
            "ai_responses_used": subscription.ai_responses_used,
            "products_fetched": subscription.products_fetched,
        }
    }

    return response_data


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current usage statistics and limits"""
    enforcement = PlanEnforcementService(db)
    limits = enforcement.get_plan_limits(current_user.id)

    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No plan found"
        )

    return {
        "templates_used": limits["usage"].get("templates_used", 0),
        "templates_limit": limits["limits"]["max_templates"],
        "rule_messages_used": limits["usage"].get("rule_messages_used", 0),
        "rule_messages_limit": limits["limits"]["max_rule_based_messages"],
        "ai_responses_used": limits["usage"].get("ai_responses_used", 0),
        "ai_responses_limit": limits["limits"]["max_ai_responses_per_session"],
        "products_fetched": limits["usage"].get("products_fetched", 0),
        "products_limit": limits["limits"]["max_products"],
    }


@router.post("/upgrade")
async def upgrade_plan(
    request: UpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upgrade or change subscription plan - bypasses Stripe for all plans"""

    # Get target plan
    target_plan = db.query(Plan).filter(
        Plan.plan_name == request.plan_name,
        Plan.is_active == True
    ).first()

    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{request.plan_name}' not found"
        )

    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    # Calculate period end (1 year for "simple conversion")
    period_end = datetime.utcnow() + timedelta(days=365)

    if not subscription:
        # Create new subscription
        subscription = Subscription(
            user_id=current_user.id,
            plan_id=target_plan.id,
            status="active",
            billing_cycle=request.billing_cycle,
            current_period_start=datetime.utcnow(),
            current_period_end=period_end,
        )
        db.add(subscription)
    else:
        # Update existing subscription
        subscription.plan_id = target_plan.id
        subscription.billing_cycle = request.billing_cycle
        subscription.status = "active"
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = period_end
        subscription.cancel_at_period_end = False

    # Update user's plan field (for backward compatibility)
    current_user.plan = request.plan_name

    db.commit()
    db.refresh(subscription)

    return {
        "success": True,
        "message": f"Successfully switched to {target_plan.display_name} plan",
        "plan": target_plan.display_name,
        "billing_cycle": request.billing_cycle
    }


@router.post("/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for paid plan upgrade"""

    # Get target plan
    target_plan = db.query(Plan).filter(
        Plan.plan_name == request.plan_name,
        Plan.is_active == True
    ).first()

    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{request.plan_name}' not found"
        )

    if target_plan.monthly_price == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free plans don't require checkout. Use /upgrade endpoint."
        )

    try:
        stripe_service = StripeService(db)
        session = stripe_service.create_checkout_session(
            user=current_user,
            plan=target_plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        return {
            "success": True,
            "checkout_url": session["url"],
            "session_id": session["session_id"]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""

    payload = await request.body()

    try:
        # Import stripe here to avoid import errors if not installed
        try:
            import stripe
        except ImportError:
            logger.error("Stripe package not installed. Run: pip install stripe")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe integration not configured"
            )

        # Verify webhook signature (if webhook secret is configured)
        from config import get_settings
        settings = get_settings()

        if hasattr(settings, 'STRIPE_WEBHOOK_SECRET') and settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # For development without webhook secret
            import json
            event = json.loads(payload)

        stripe_service = StripeService(db)

        # Handle different event types
        if event["type"] == "checkout.session.completed":
            stripe_service.handle_checkout_completed(event["data"]["object"])
            logger.info(f"Processed checkout.session.completed")

        elif event["type"] == "customer.subscription.updated":
            stripe_service.handle_subscription_updated(event["data"]["object"])
            logger.info(f"Processed customer.subscription.updated")

        elif event["type"] == "customer.subscription.deleted":
            stripe_service.handle_subscription_deleted(event["data"]["object"])
            logger.info(f"Processed customer.subscription.deleted")

        elif event["type"] == "invoice.payment_failed":
            # Handle failed payment
            subscription_id = event["data"]["object"].get("subscription")
            if subscription_id:
                subscription = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == subscription_id
                ).first()
                if subscription:
                    subscription.status = "past_due"
                    db.commit()
                    logger.warning(f"Payment failed for subscription {subscription_id}")

        return {"status": "success"}

    except ImportError as e:
        logger.error(f"Stripe not installed: {e}")
        raise HTTPException(status_code=500, detail="Stripe integration not available")
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/cancel")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel subscription at end of billing period"""

    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    if subscription.plan.plan_name == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel free plan"
        )

    # Mark for cancellation at period end
    subscription.cancel_at_period_end = True
    subscription.canceled_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Subscription will be canceled at the end of the current billing period",
        "cancel_at": subscription.current_period_end
    }


@router.post("/reactivate")
async def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate a canceled subscription"""

    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    if not subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not scheduled for cancellation"
        )

    # Remove cancellation flag
    subscription.cancel_at_period_end = False
    subscription.canceled_at = None

    db.commit()

    return {
        "success": True,
        "message": "Subscription reactivated successfully"
    }


@router.get("/limits")
async def get_plan_limits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed plan limits and features"""
    enforcement = PlanEnforcementService(db)
    limits = enforcement.get_plan_limits(current_user.id)

    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No plan found"
        )

    return limits


@router.get("/plan-limits")
async def get_plan_limits_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed plan limits and features (alias endpoint for frontend)"""
    enforcement = PlanEnforcementService(db)
    limits = enforcement.get_plan_limits(current_user.id)

    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No plan found"
        )

    return limits
