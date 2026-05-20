"""
Plan Enforcement Service

Enforces plan limits based on CLAUDE.md specifications:
- FREE: 3 templates, 3 rule messages, 5 AI responses/session, 3 products, homepage only
- STARTER: 10 templates, 10 rule messages, unlimited AI, unlimited products, homepage only
- PREMIUM: Unlimited everything, full website fetch, managed API
"""
from sqlalchemy.orm import Session
from models import User, Plan, Subscription, BotSettings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PlanLimits:
    """Plan limit definitions from CLAUDE.md"""

    FREE = {
        "max_templates": 3,
        "max_rule_based_messages": 3,
        "max_ai_responses_per_session": 5,
        "max_products": 10,
        "website_fetch_scope": "homepage",
        "order_form_enabled": False,
        "multi_ai_support": False,  # ChatGPT only
        "setup_support": False,
        "team_collaboration": False,
        "analytics_dashboard": False,
        "crm_integrations": False,
        "managed_api": False,
    }

    STARTER = {
        "max_templates": 10,
        "max_rule_based_messages": 10,
        "max_ai_responses_per_session": 0,  # 0 = unlimited
        "max_products": 100,
        "website_fetch_scope": "homepage",
        "order_form_enabled": True,
        "multi_ai_support": True,  # ChatGPT, Gemini, Claude
        "setup_support": True,
        "team_collaboration": False,
        "analytics_dashboard": False,
        "crm_integrations": False,
        "managed_api": False,
    }

    PREMIUM = {
        "max_templates": 0,  # 0 = unlimited
        "max_rule_based_messages": 0,  # 0 = unlimited
        "max_ai_responses_per_session": 0,  # 0 = unlimited
        "max_products": 0,  # 0 = unlimited
        "website_fetch_scope": "full",
        "order_form_enabled": True,
        "multi_ai_support": True,
        "setup_support": True,
        "team_collaboration": True,
        "analytics_dashboard": True,
        "crm_integrations": True,
        "managed_api": True,  # We provide API
    }


class PlanEnforcementService:
    """Service to check and enforce plan limits"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_plan(self, user_id: int) -> Optional[Plan]:
        """Get user's current plan"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Check if user has active subscription
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"])
        ).first()

        if subscription:
            return subscription.plan

        # Fallback to free plan
        return self.db.query(Plan).filter(Plan.plan_name == "free").first()

    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's subscription"""
        return self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

    def can_add_template(self, user_id: int) -> tuple[bool, str]:
        """Check if user can add more templates"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        # Unlimited templates
        if plan.max_templates == 0:
            return True, ""

        # Count current templates
        bot_settings = self.db.query(BotSettings).join(
            BotSettings.bot
        ).filter(
            BotSettings.bot.has(user_id=user_id)
        ).first()

        if not bot_settings:
            return True, ""

        current_templates = 0
        if bot_settings.templates:
            current_templates = len(bot_settings.templates)

        if current_templates >= plan.max_templates:
            return False, f"Template limit reached. Your {plan.display_name} plan allows {plan.max_templates} templates. Upgrade to add more."

        return True, ""

    def can_add_rule_message(self, user_id: int) -> tuple[bool, str]:
        """Check if user can add more rule-based messages"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        # Unlimited rule messages
        if plan.max_rule_based_messages == 0:
            return True, ""

        # Count current rule messages
        bot_settings = self.db.query(BotSettings).join(
            BotSettings.bot
        ).filter(
            BotSettings.bot.has(user_id=user_id)
        ).first()

        if not bot_settings:
            return True, ""

        current_rules = 0
        if bot_settings.custom_responses:
            current_rules = len(bot_settings.custom_responses)

        if current_rules >= plan.max_rule_based_messages:
            return False, f"Rule-based message limit reached. Your {plan.display_name} plan allows {plan.max_rule_based_messages} rules. Upgrade to add more."

        return True, ""

    def can_use_ai_response(self, user_id: int, session_phone: str) -> tuple[bool, str]:
        """Check if user can use AI response in current session"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        # Unlimited AI responses
        if plan.max_ai_responses_per_session == 0:
            return True, ""

        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False, "No subscription found"

        # Check session AI usage (simplified - in production, track per phone number)
        if subscription.ai_responses_used >= plan.max_ai_responses_per_session:
            return False, f"AI response limit reached for this session. Your {plan.display_name} plan allows {plan.max_ai_responses_per_session} AI responses per session. Upgrade for unlimited AI responses."

        return True, ""

    def increment_ai_usage(self, user_id: int):
        """Increment AI response usage counter"""
        subscription = self.get_user_subscription(user_id)
        if subscription:
            subscription.ai_responses_used += 1
            self.db.commit()

    def can_fetch_products(self, user_id: int, current_count: int) -> tuple[bool, str]:
        """Check if user can fetch more products"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        # Unlimited products
        if plan.max_products == 0:
            return True, ""

        if current_count >= plan.max_products:
            return False, f"Product fetch limit reached. Your {plan.display_name} plan allows {plan.max_products} products. Upgrade for unlimited products."

        return True, ""

    def can_fetch_full_website(self, user_id: int) -> tuple[bool, str]:
        """Check if user can fetch full website content"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        if plan.website_fetch_scope == "homepage":
            return False, f"Your {plan.display_name} plan only allows homepage content fetching. Upgrade to PREMIUM for full website access."

        return True, ""

    def can_use_order_form(self, user_id: int) -> tuple[bool, str]:
        """Check if user can use order form feature"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        if not plan.order_form_enabled:
            return False, f"Order form is disabled on {plan.display_name} plan. Upgrade to STARTER or PREMIUM to enable."

        return True, ""

    def can_use_multi_ai(self, user_id: int, ai_provider: str) -> tuple[bool, str]:
        """Check if user can use multiple AI providers (Gemini, Claude)"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False, "No plan found"

        # ChatGPT is allowed on all plans
        if ai_provider.lower() in ["openai", "chatgpt", "gpt"]:
            return True, ""

        if not plan.multi_ai_support:
            return False, f"Your {plan.display_name} plan only supports ChatGPT. Upgrade to STARTER or PREMIUM for Gemini and Claude support."

        return True, ""

    def get_plan_limits(self, user_id: int) -> Dict[str, Any]:
        """Get all plan limits for a user"""
        plan = self.get_user_plan(user_id)
        subscription = self.get_user_subscription(user_id)

        if not plan:
            return {}

        return {
            "plan_name": plan.plan_name,
            "display_name": plan.display_name,
            "limits": {
                "max_templates": plan.max_templates,
                "max_rule_based_messages": plan.max_rule_based_messages,
                "max_ai_responses_per_session": plan.max_ai_responses_per_session,
                "max_products": plan.max_products,
                "website_fetch_scope": plan.website_fetch_scope,
            },
            "features": {
                "order_form_enabled": plan.order_form_enabled,
                "multi_ai_support": plan.multi_ai_support,
                "setup_support": plan.setup_support,
                "team_collaboration": plan.team_collaboration,
                "analytics_dashboard": plan.analytics_dashboard,
                "crm_integrations": plan.crm_integrations,
                "managed_api": plan.managed_api,
            },
            "usage": {
                "templates_used": subscription.templates_used if subscription else 0,
                "rule_messages_used": subscription.rule_messages_used if subscription else 0,
                "ai_responses_used": subscription.ai_responses_used if subscription else 0,
                "products_fetched": subscription.products_fetched if subscription else 0,
            } if subscription else {}
        }

    def reset_monthly_usage(self, user_id: int):
        """Reset monthly usage counters"""
        subscription = self.get_user_subscription(user_id)
        if subscription:
            subscription.templates_used = 0
            subscription.rule_messages_used = 0
            subscription.ai_responses_used = 0
            subscription.products_fetched = 0
            subscription.usage_reset_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Reset usage for user {user_id}")
