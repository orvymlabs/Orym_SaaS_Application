"""
Bot Engine — Intelligent Routing with Plan-based Feature Gating (No Product Features)
"""
import re
import logging
from datetime import datetime
from typing import Optional
from .default_bot import process as default_process, _get_contact_info, _get_services
from .ai_service import ai_reply

logger = logging.getLogger(__name__)

PLAN_ERROR = "⚠️ This feature is available in Growth plan. Please upgrade."

# Notification message when AI limit is hit
AI_LIMIT_NOTIFICATION = "⚠️ AI limit reached. Switching to keyword-based responses. Upgrade your plan for more AI messages."


def _fallback_to_predefined(bot_settings: dict, text: str, name: str, phone: str, ai_limit_exceeded: bool = False) -> str:
    """Fallback to predefined/custom responses when AI fails or limit is reached."""
    custom = bot_settings.get("custom_responses") or {}
    tl = text.lower().strip()

    # Build notification prefix if AI limit was exceeded
    notification = ""
    if ai_limit_exceeded:
        notification = AI_LIMIT_NOTIFICATION

    # Try exact match first
    if tl in custom:
        return notification + custom[tl].replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

    # Try contains match
    for keyword, response in custom.items():
        if keyword.startswith("template_"):
            continue
        if keyword.lower() in tl:
            return notification + response.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

    # No custom rule matched - return generic fallback
    if ai_limit_exceeded:
        return notification + "I'm now using keyword-based responses. Type a keyword like 'menu', 'services', or 'contact' for help."
    return "I'm having trouble connecting to my brain. Please try again in a moment!"


def _is_website_query(text: str) -> bool:
    tl = text.lower()
    return any(w in tl for w in ['about', 'contact', 'service', 'services', 'address', 'phone', 'email', 'location', 'website', 'info'])


def _capture_lead(bot_id: int, phone: str, name: str, text: str):
    """Capture or update lead with latest message and detect interest level."""
    from models import Lead
    from database import SessionLocal

    # Interest keywords that indicate buying intent
    interest_keywords = ['price', 'cost', 'buy', 'order', 'purchase', 'interested', 'how much',
                         'quote', 'delivery', 'shipping', 'contact', 'call', 'email', 'phone',
                         'address', 'location', 'visit', 'see', 'demo', 'trial', 'sample',
                         'available', 'stock', 'in stock', 'when can', 'how to', 'need', 'want']

    tl = text.lower()
    is_interested = any(keyword in tl for keyword in interest_keywords)

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        if not lead:
            # New lead
            context = {
                "step": "active",
                "interest_level": "high" if is_interested else "medium",
                "last_query": text[:200]
            }
            lead = Lead(bot_id=bot_id, phone=phone, name=name, last_message=text, context=context)
            db.add(lead)
            logger.info(f"🎯 New lead captured: {phone} (Interest: {context['interest_level']})")
        else:
            # Update existing lead
            lead.last_message = text
            lead.name = name or lead.name

            # Update context with interest tracking
            context = lead.context or {}
            context["last_query"] = text[:200]
            if is_interested:
                context["interest_level"] = "high"
                context["interested_at"] = str(datetime.now())
        lead.context = context

        db.commit()
    except Exception as e:
        logger.error(f"Failed to capture lead: {e}")
        db.rollback()
    finally:
        db.close()


def handle_message(bot_mode: str, bot_id: int, text: str, phone: str, name: str,
                   bot_settings: dict, integrations: dict, contact_info: dict,
                   products: list, categories: list, business_type: str = "product",
                   user_plan: str = "starter", user_id: int = None) -> str:

    from models import Lead
    from database import SessionLocal

    # Capture lead for ALL modes (universal lead capture)
    _capture_lead(bot_id, phone, name, text)

    # Ensure last_active_at is set in context for inactivity tracking
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        if lead:
            context = lead.context or {}
            context["last_active_at"] = str(datetime.now())
            lead.context = context
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update last_active_at: {e}")
        db.rollback()
    finally:
        db.close()

    tl = text.lower().strip()
    lang = bot_settings.get("language", "english")
    api_key = bot_settings.get("api_key", "")
    provider = bot_settings.get("model_name", "openrouter")
    specific_model = bot_settings.get("specific_model_name") or provider
    prompt = bot_settings.get("prompt", "")
    temp = min(max(bot_settings.get("temperature", 70) / 100.0, 0.0), 1.0)

    logger.info(f"🧠 Routing message (Mode={bot_mode}, Type={business_type}, Plan={user_plan}, Input='{text}')")

    # DEFAULT MODE
    if bot_mode == "default":
        return default_process(
            bot_id, text, phone, name,
            business_type=business_type,
            user_plan=user_plan,
            products=products,
            contact_info=contact_info,
            user_id=user_id
        )

    # PREDEFINED MODE
    if bot_mode == "predefined":

        # Handle menu navigation (1, 2, 3)
        if tl.startswith("1") or tl == "service" or tl == "services":
            return _get_services(bot_settings)

        elif tl.startswith("2") or tl == "delivery" or "shipping" in tl:
            from .default_bot import _get_delivery_info
            return _get_delivery_info(bot_settings)

        elif tl.startswith("3") or tl == "contact":
            return _get_contact_info(bot_settings, contact_info, phone=phone, name=name)

        # Handle general website queries
        if _is_website_query(text):
            if "service" in tl or business_type == "service":
                return _get_services(bot_settings)
            return _get_contact_info(bot_settings, contact_info, phone=phone, name=name)

        # Keyword Engine logic - match custom user-defined rules
        # custom_responses contains user's keyword -> response mappings
        custom = bot_settings.get("custom_responses") or {}

        # First, try exact match
        if tl in custom:
            return custom[tl].replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

        # Then, try contains match (keyword appears anywhere in user's message)
        for keyword, response in custom.items():
            # Skip template keys (they start with "template_")
            if keyword.startswith("template_"):
                continue
            if keyword.lower() in tl:
                return response.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

        # AI Fallback if API key exists (optional - can be removed if you want strict keyword-only mode)
        if api_key:
            ai_resp = ai_reply(text, lang, api_key, provider, prompt, temp, contact_info, products, categories, model_name=specific_model, business_type=business_type)
            if ai_resp:
                return ai_resp

        # Default fallback - show menu
        return "I'm sorry, I couldn't find that information. Type *menu* to see available options."

    # AI MODE
    if bot_mode == "ai":
        if not api_key:
            return "⚠️ AI assistant is not configured. Please add your API key in settings."

        # Check AI usage limit before calling AI
        ai_limit_reached = False
        if user_id:
            from models import Usage
            from database import SessionLocal
            db = SessionLocal()
            try:
                usage = db.query(Usage).filter(Usage.user_id == user_id).first()
                if usage and usage.ai_requests_made >= usage.ai_limit:
                    ai_limit_reached = True
                    logger.warning(f"AI limit reached for user {user_id}: {usage.ai_requests_made}/{usage.ai_limit}")
            except Exception as e:
                logger.error(f"Error checking AI limit: {e}")
            finally:
                db.close()

        if ai_limit_reached:
            # Fallback to predefined mode with notification
            logger.info(f"AI limit reached - falling back to predefined mode for user {user_id}")
            return _fallback_to_predefined(bot_settings, text, name, phone, ai_limit_exceeded=True)

        ai_resp = ai_reply(
            text, lang, api_key, provider, prompt, temp,
            contact_info, products, categories,
            model_name=specific_model,
            business_type=business_type,
            user_plan=user_plan
        )

        if ai_resp:
            return ai_resp

        # AI failed - fallback to predefined custom rules
        logger.info(f"AI failed to respond - falling back to predefined mode")
        return _fallback_to_predefined(bot_settings, text, name, phone, ai_limit_exceeded=ai_limit_reached)

    return default_process(
        bot_id, text, phone, name,
        business_type=business_type,
        user_plan=user_plan,
        products=products,
        contact_info=contact_info,
        user_id=user_id
    )