"""
Stripe Payment Integration Service

Handles:
- Creating Stripe customers
- Creating checkout sessions for subscriptions
- Managing subscription lifecycle
- Processing webhooks
"""
import stripe
from config import get_settings
from models import User, Subscription, Plan
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


class StripeService:
    """Service for Stripe payment operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_customer(self, user: User) -> str:
        """Get existing Stripe customer or create new one"""
        if user.stripe_customer_id:
            return user.stripe_customer_id

        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name or user.email,
                metadata={"user_id": user.id}
            )
            user.stripe_customer_id = customer.id
            self.db.commit()
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    def create_checkout_session(
        self,
        user: User,
        plan: Plan,
        success_url: str,
        cancel_url: str
    ) -> dict:
        """Create Stripe Checkout session for subscription"""

        if not stripe.api_key:
            raise ValueError("Stripe API key not configured")

        if plan.monthly_price == 0:
            raise ValueError("Cannot create checkout for free plan")

        customer_id = self.get_or_create_customer(user)

        try:
            # Create or get Stripe price
            if not plan.stripe_price_id:
                price = stripe.Price.create(
                    unit_amount=int(plan.monthly_price * 100),  # Convert to cents
                    currency="usd",
                    recurring={"interval": "month"},
                    product_data={
                        "name": f"ORVYM NEXUS {plan.display_name}",
                        "description": f"{plan.display_name} Plan - AI WhatsApp Bot"
                    },
                )
                plan.stripe_price_id = price.id
                self.db.commit()
                logger.info(f"Created Stripe price {price.id} for plan {plan.plan_name}")

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": plan.stripe_price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata={
                    "user_id": user.id,
                    "plan_id": plan.id,
                    "plan_name": plan.plan_name,
                },
                subscription_data={
                    "metadata": {
                        "user_id": user.id,
                        "plan_id": plan.id,
                    }
                },
                allow_promotion_codes=True,
            )

            logger.info(f"Created checkout session {session.id} for user {user.id}")
            return {
                "session_id": session.id,
                "url": session.url,
            }

        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    def handle_checkout_completed(self, session: dict):
        """Handle successful checkout completion"""
        try:
            user_id = int(session["metadata"]["user_id"])
            plan_id = int(session["metadata"]["plan_id"])
            stripe_subscription_id = session["subscription"]

            # Get Stripe subscription details
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)

            # Update or create subscription
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if subscription:
                subscription.plan_id = plan_id
                subscription.stripe_subscription_id = stripe_subscription_id
                subscription.stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
                subscription.status = stripe_sub["status"]
                subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
                subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
                subscription.cancel_at_period_end = False
            else:
                subscription = Subscription(
                    user_id=user_id,
                    plan_id=plan_id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_price_id=stripe_sub["items"]["data"][0]["price"]["id"],
                    status=stripe_sub["status"],
                    billing_cycle="monthly",
                    current_period_start=datetime.fromtimestamp(stripe_sub["current_period_start"]),
                    current_period_end=datetime.fromtimestamp(stripe_sub["current_period_end"]),
                )
                self.db.add(subscription)

            # Update user plan
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
                if plan:
                    user.plan = plan.plan_name

            self.db.commit()
            logger.info(f"Subscription created/updated for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to handle checkout completion: {e}")
            self.db.rollback()
            raise

    def handle_subscription_updated(self, subscription_data: dict):
        """Handle subscription update webhook"""
        try:
            stripe_subscription_id = subscription_data["id"]

            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()

            if not subscription:
                logger.warning(f"Subscription {stripe_subscription_id} not found in database")
                return

            subscription.status = subscription_data["status"]
            subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
            subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)

            if subscription_data.get("canceled_at"):
                subscription.canceled_at = datetime.fromtimestamp(subscription_data["canceled_at"])

            self.db.commit()
            logger.info(f"Updated subscription {stripe_subscription_id}")

        except Exception as e:
            logger.error(f"Failed to handle subscription update: {e}")
            self.db.rollback()
            raise

    def handle_subscription_deleted(self, subscription_data: dict):
        """Handle subscription cancellation webhook"""
        try:
            stripe_subscription_id = subscription_data["id"]

            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()

            if not subscription:
                logger.warning(f"Subscription {stripe_subscription_id} not found")
                return

            # Downgrade to free plan
            free_plan = self.db.query(Plan).filter(Plan.plan_name == "free").first()
            if free_plan:
                subscription.plan_id = free_plan.id
                subscription.status = "canceled"

                # Update user plan
                user = self.db.query(User).filter(User.id == subscription.user_id).first()
                if user:
                    user.plan = "free"

            self.db.commit()
            logger.info(f"Subscription {stripe_subscription_id} canceled, downgraded to free")

        except Exception as e:
            logger.error(f"Failed to handle subscription deletion: {e}")
            self.db.rollback()
            raise

    def cancel_subscription(self, subscription: Subscription, immediate: bool = False):
        """Cancel a Stripe subscription"""
        if not subscription.stripe_subscription_id:
            raise ValueError("No Stripe subscription ID found")

        try:
            if immediate:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = "canceled"
                subscription.canceled_at = datetime.utcnow()
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
                subscription.canceled_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Canceled subscription {subscription.stripe_subscription_id}")

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
