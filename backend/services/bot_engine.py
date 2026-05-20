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

PLAN_ERROR = "⚠️ This feature is available in Starter or Premium plan. Please upgrade."

# Notification message when AI limit is hit
AI_LIMIT_NOTIFICATION = "⚠️ AI limit reached. Switching to keyword-based responses. Upgrade your plan for more AI messages."


def _fallback_to_predefined(bot_settings: dict, text: str, name: str, phone: str, ai_limit_exceeded: bool = False, silent_fallback: bool = False) -> str:
    """Fallback to predefined/custom responses when AI fails or limit is reached."""
    custom = bot_settings.get("custom_responses") or {}
    tl = text.lower().strip()

    # Try exact match first
    if tl in custom:
        return custom[tl].replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

    # Try contains match
    for keyword, response in custom.items():
        if keyword.startswith("template_"):
            continue
        if keyword.lower() in tl:
            return response.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

    # No custom rule matched - check if there's a custom fallback message
    fallback_message = bot_settings.get("fallback_message")
    if fallback_message:
        return fallback_message.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

    # If no custom responses configured, return empty string to trigger default mode (menu)
    # This ensures users see their configured predefined responses or default menu, not hardcoded messages
    return ""


def _is_website_query(text: str) -> bool:
    tl = text.lower()
    return any(w in tl for w in ['about', 'contact', 'service', 'services', 'address', 'phone', 'email', 'location', 'website', 'info'])


def _capture_lead(bot_id: int, phone: str, name: str, text: str):
    """Capture or update lead with latest message and detect interest level."""
    from models import Lead, Bot
    from database import SessionLocal
    from sqlalchemy.orm.attributes import flag_modified
    from routers.notifications import create_notification

    logger.info(f"🎯 LEAD CAPTURE CALLED: bot_id={bot_id}, phone={phone}, name={name}, text='{text[:50]}...'")

    # Trivial greetings that should NOT create leads
    trivial_greetings = ['hi', 'hello', 'hey', 'hii', 'hiii', 'helo', 'hola', 'yo', 'sup', 'wassup', 'start', 'menu']

    tl = text.lower().strip()

    # Don't create new leads for trivial greetings
    if tl in trivial_greetings:
        logger.info(f"⏭️ Skipping lead capture for {phone} - trivial greeting: '{text}'")
        return

    db = SessionLocal()
    try:
        # Check if user is currently in ordering flow - if so, skip lead capture
        existing_lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        if existing_lead and existing_lead.context:
            current_step = existing_lead.context.get("step")
            if current_step == "ordering":
                logger.info(f"⏭️ Skipping lead capture for {phone} - user is in ordering flow")
                db.close()
                return

        # Interest keywords that indicate buying intent (excluding "order" to avoid confusion with order flow)
        interest_keywords = ['price', 'cost', 'buy', 'purchase', 'interested', 'how much',
                             'quote', 'delivery', 'shipping', 'contact', 'call', 'email', 'phone',
                             'address', 'location', 'visit', 'see', 'demo', 'trial', 'sample',
                             'available', 'stock', 'in stock', 'when can', 'how to', 'need', 'want',
                             'product', 'service', 'about', 'info', 'information', 'details']

        is_interested = any(keyword in tl for keyword in interest_keywords)
        logger.info(f"🔍 Interest detection for {phone}: is_interested={is_interested}, text='{text[:50]}...'")

        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        is_new_lead = lead is None

        if not lead:
            # Only create new lead if user shows interest
            if not is_interested:
                logger.info(f"⏭️ Not creating lead for {phone} - no interest keywords detected in: '{text}'")
                return

            # New lead with interest
            context = {
                "step": "active",
                "interest_level": "high" if is_interested else "medium",
                "last_query": text[:200],
                "last_active_at": str(datetime.now())
            }
            lead = Lead(bot_id=bot_id, phone=phone, name=name, last_message=text, context=context)
            db.add(lead)
            logger.info(f"✅ NEW LEAD CAPTURED: {phone} - {name} (Interest: {context['interest_level']})")
        else:
            # Update existing lead ONLY if message shows interest AND not in ordering flow
            if not is_interested:
                logger.info(f"⏭️ Not updating lead for {phone} - no interest keywords in: '{text}'")
                return

            # Update existing lead with meaningful message
            lead.last_message = text
            lead.name = name or lead.name

            # Update context with interest tracking (preserve step if it exists)
            context = lead.context or {}
            context["last_query"] = text[:200]
            context["last_active_at"] = str(datetime.now())
            context["interest_level"] = "high"
            context["interested_at"] = str(datetime.now())

            lead.context = context
            # Mark JSON field as modified so SQLAlchemy detects the change
            flag_modified(lead, 'context')
            logger.info(f"✅ LEAD UPDATED: {phone} - {name} (Interest: high)")

        db.commit()

        # Create notification for new lead or lead activity
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                if is_new_lead:
                    create_notification(
                        db=db,
                        user_id=bot.user_id,
                        type="new_lead",
                        title="New Lead Captured",
                        message=f"New lead from {phone} - {name or 'Unknown'}: {text[:50]}..."
                    )
                    logger.info(f"📬 Notification created for new lead: {phone}")
                else:
                    # Notification for existing lead showing interest
                    create_notification(
                        db=db,
                        user_id=bot.user_id,
                        type="new_lead",
                        title="Lead Activity",
                        message=f"Lead {phone} - {name or 'Unknown'} showed interest: {text[:50]}..."
                    )
                    logger.info(f"📬 Notification created for lead activity: {phone}")
        except Exception as e:
            logger.error(f"Failed to create lead notification: {e}")

    except Exception as e:
        logger.error(f"❌ Failed to capture lead: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def handle_message(bot_mode: str, bot_id: int, text: str, phone: str, name: str,
                   bot_settings: dict, integrations: dict, contact_info: dict,
                   products: list, categories: list, business_type: str = "product",
                   user_plan: str = "starter", user_id: int = None) -> str:

    # Capture lead for ALL modes (universal lead capture)
    # This also updates last_active_at in the context
    _capture_lead(bot_id, phone, name, text)

    tl = text.lower().strip()
    
    # Enforce plan limits for bot engine
    # FREE: 3 templates, 3 rules
    # STARTER: 10 templates, 10 rules
    # PREMIUM: Unlimited
    
    plan_name = (user_plan or "free").lower()
    max_templates = 3 if plan_name == "free" else (10 if plan_name == "starter" else 0)
    max_rules = 3 if plan_name == "free" else (10 if plan_name == "starter" else 0)
    
    lang = bot_settings.get("language", "english")
    api_key = bot_settings.get("api_key", "")
    provider = bot_settings.get("model_name", "openrouter")
    specific_model = bot_settings.get("specific_model_name") or provider
    prompt = bot_settings.get("prompt", "")
    temp = min(max(bot_settings.get("temperature", 70) / 100.0, 0.0), 1.0)

    logger.info(f"🧠 Routing message (Mode={bot_mode}, Type={business_type}, Plan={user_plan}, Input='{text}')")
    logger.info(f"🔑 API Key present: {bool(api_key)}, Provider: {provider}, Model: {specific_model}")

    # DEFAULT MODE
    if bot_mode == "default":
        return default_process(
            bot_id, text, phone, name,
            business_type=business_type,
            user_plan=user_plan,
            products=products,
            contact_info=contact_info,
            user_id=user_id,
            bot_settings=bot_settings
        )

    # PREDEFINED MODE
    if bot_mode == "predefined":

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

        # Check for custom fallback message
        fallback_message = bot_settings.get("fallback_message")
        if fallback_message:
            return fallback_message.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

        # If no custom fallback, return empty to trigger default mode
        return ""

    # AI MODE
    if bot_mode == "ai":
        # Check if API key exists FIRST
        if not api_key or not api_key.strip():
            logger.error(f"AI mode selected but no API key configured for bot {bot_id}")
            # Return clear error message instead of falling back to templates
            return "⚠️ AI Mode is enabled but no API key is configured. Please add your API key in Bot Settings to use AI responses."

        # In AI mode, let AI handle ALL messages including greetings
        # Only show menu if user explicitly types "menu"
        if tl == "menu":
            return default_process(
                bot_id, text, phone, name,
                business_type=business_type,
                user_plan=user_plan,
                products=products,
                contact_info=contact_info,
                user_id=user_id,
                bot_settings=bot_settings
            )

        # Check AI usage limit using plan enforcement service
        ai_limit_reached = False
        if user_id:
            from services.plan_enforcement import PlanEnforcementService
            from database import SessionLocal
            from routers.notifications import create_notification
            db = SessionLocal()
            try:
                plan_service = PlanEnforcementService(db)
                can_use, error_msg = plan_service.can_use_ai_response(user_id, phone)

                if not can_use:
                    ai_limit_reached = True
                    logger.warning(f"AI limit reached for user {user_id}: {error_msg}")

                    # Create notification for user dashboard
                    try:
                        user_plan_info = plan_service.get_user_plan(user_id)
                        create_notification(
                            db=db,
                            user_id=user_id,
                            type="ai_limit_exceeded",
                            title="AI Limit Reached",
                            message=f"Your AI response limit has been reached. {error_msg}"
                        )
                        logger.info(f"Created AI limit notification for user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to create AI limit notification: {e}")
            except Exception as e:
                logger.error(f"Error checking AI limit: {e}")
            finally:
                db.close()

        if ai_limit_reached:
            # Fallback to predefined mode with notification
            logger.info(f"AI limit reached - falling back to predefined mode for user {user_id}")
            return _fallback_to_predefined(bot_settings, text, name, phone, ai_limit_exceeded=True, silent_fallback=True)

        ai_resp = ai_reply(
            text, lang, api_key, provider, prompt, temp,
            contact_info, products, categories,
            model_name=specific_model,
            business_type=business_type,
            user_plan=user_plan
        )

        # Increment AI usage counter after successful response
        if ai_resp and not ai_resp.startswith("API_") and user_id:
            from services.plan_enforcement import PlanEnforcementService
            from database import SessionLocal
            db = SessionLocal()
            try:
                plan_service = PlanEnforcementService(db)
                plan_service.increment_ai_usage(user_id)
                logger.info(f"Incremented AI usage for user {user_id}")
            except Exception as e:
                logger.error(f"Error incrementing AI usage: {e}")
            finally:
                db.close()

        # Check for API error codes
        if ai_resp and ai_resp.startswith("API_"):
            # External AI API error occurred - create notification
            if user_id:
                from models import Usage
                from database import SessionLocal
                from routers.notifications import create_notification
                db = SessionLocal()
                try:
                    error_messages = {
                        "API_RATE_LIMIT_EXCEEDED": {
                            "title": "AI API Rate Limit Exceeded",
                            "message": f"Your {provider.upper()} API rate limit has been exceeded. Please wait a few minutes or check your API provider dashboard."
                        },
                        "API_QUOTA_EXCEEDED": {
                            "title": "AI API Quota Exceeded",
                            "message": f"Your {provider.upper()} API quota/credits have been exhausted. Please add credits to your API provider account or upgrade your plan."
                        },
                        "API_INVALID_KEY": {
                            "title": "Invalid AI API Key",
                            "message": f"Your {provider.upper()} API key is invalid or has been revoked. Please update your API key in Bot Engine settings."
                        },
                        "API_TIMEOUT": {
                            "title": "AI API Timeout",
                            "message": f"The {provider.upper()} API request timed out. This may be temporary - please try again."
                        }
                    }

                    error_info = error_messages.get(ai_resp, {
                        "title": "AI API Error",
                        "message": f"An error occurred with your {provider.upper()} API. Please check your API key and account status."
                    })

                    create_notification(
                        db=db,
                        user_id=user_id,
                        type="ai_api_error",
                        title=error_info["title"],
                        message=error_info["message"]
                    )
                    logger.info(f"Created AI API error notification for user {user_id}: {ai_resp}")
                except Exception as e:
                    logger.error(f"Failed to create AI API error notification: {e}")
                finally:
                    db.close()

            # Fallback to keyword trigger mode - silent for WhatsApp users (no error message shown)
            logger.info(f"AI API error ({ai_resp}) - falling back to keyword trigger mode silently")
            return _fallback_to_predefined(bot_settings, text, name, phone, ai_limit_exceeded=False, silent_fallback=True)

        if ai_resp:
            # Increment AI usage counter
            if user_id:
                from models import Usage
                from database import SessionLocal
                db = SessionLocal()
                try:
                    usage = db.query(Usage).filter(Usage.user_id == user_id).first()
                    if usage:
                        usage.ai_requests_made += 1
                        db.commit()
                        logger.info(f"Incremented AI usage for user {user_id}: {usage.ai_requests_made}/{usage.ai_limit}")
                except Exception as e:
                    logger.error(f"Failed to increment AI usage: {e}")
                finally:
                    db.close()
            return ai_resp

        # AI failed to respond (returned None) - create notification and fallback
        logger.warning(f"AI failed to respond (returned None) for user {user_id}")

        if user_id:
            from models import Usage
            from database import SessionLocal
            from routers.notifications import create_notification
            db = SessionLocal()
            try:
                create_notification(
                    db=db,
                    user_id=user_id,
                    type="ai_api_error",
                    title="AI Not Responding",
                    message=f"Your {provider.upper()} AI is not responding. Please check your API key and account status. The bot is now using keyword-based responses."
                )
                logger.info(f"Created AI failure notification for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create AI failure notification: {e}")
            finally:
                db.close()

        # Fallback to keyword trigger mode silently
        logger.info(f"AI failed to respond - falling back to keyword trigger mode with custom_responses")
        logger.info(f"Available custom_responses: {list(bot_settings.get('custom_responses', {}).keys())}")
        return _fallback_to_predefined(bot_settings, text, name, phone, ai_limit_exceeded=ai_limit_reached, silent_fallback=True)

    return default_process(
        bot_id, text, phone, name,
        business_type=business_type,
        user_plan=user_plan,
        products=products,
        contact_info=contact_info,
        user_id=user_id,
        bot_settings=bot_settings
    )