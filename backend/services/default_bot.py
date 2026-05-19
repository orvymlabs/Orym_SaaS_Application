"""
Default Bot Engine — Template-based flow with Order Capture
Optimized with caching and fresh database lookups.
"""
import re
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

# Configure Logging
logger = logging.getLogger(__name__)

# Global In-Memory Cache for Bot Settings
_bot_settings_cache: Dict[int, Dict[str, Any]] = {}
_cache_lock = threading.Lock()

def clear_cache_for_bot(bot_id: int):
    """Clear in-memory settings cache for a specific bot."""
    with _cache_lock:
        if bot_id in _bot_settings_cache:
            del _bot_settings_cache[bot_id]
            logger.info(f"Cache cleared for bot {bot_id}")

def refresh_cache(bot_id: int, *args, **kwargs):
    """Alias for clear_cache_for_bot to match integration router calls."""
    clear_cache_for_bot(bot_id)

# ===================== UI HELPERS =====================

def _get_greeting(name, site_name, bot_settings):
    """Get greeting template from provided settings."""
    custom = None
    enabled = True
    
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
    enabled = templates.get("template_greeting_enabled", True)
    if not enabled:
        return None
    
    custom = templates.get("template_greeting")

    if custom:
        return custom.replace("{user_name}", name or "there").replace("{site_name}", site_name or "our business")

    # No default fallback - return None if no custom greeting
    return None

def _get_menu(business_type, bot_settings, site_name, user_id=None):
    """Get menu template with dynamic options based on custom templates."""
    from models import UserTemplate
    from database import SessionLocal

    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    # Check if menu is enabled
    enabled = templates.get("template_menu_enabled", True)
    if not enabled:
        return None

    # Check if there's a custom menu saved (legacy)
    custom = templates.get("template_menu")
    if custom:
        return custom

    # Fetch user's custom templates from database
    if user_id:
        db = SessionLocal()
        try:
            custom_templates = db.query(UserTemplate).filter(
                UserTemplate.user_id == user_id
            ).order_by(UserTemplate.position).all()

            if custom_templates:
                # Build menu from custom templates (no numbers, just names)
                menu_items = [f"• {t.template_name}" for t in custom_templates]

                # Check if order form is enabled and add it to menu
                order_form_enabled = bot_settings.get("order_form_enabled", True)
                form_label = bot_settings.get("form_menu_label")

                # Only add form to menu if both enabled AND custom label is set
                if order_form_enabled and form_label and form_label.strip():
                    menu_items.append(f"• {form_label}")

                items_str = "\n".join(menu_items)
                return f"*Main Menu*\n\n{items_str}\n\nType the name of any option to continue!"
        except Exception as e:
            logger.error(f"Error fetching custom templates: {e}")
        finally:
            db.close()

    # If no custom templates, show simple menu only if order form is enabled
    order_form_enabled = bot_settings.get("order_form_enabled", True)
    if order_form_enabled:
        # Use custom label - no fallback
        form_label = bot_settings.get("form_menu_label")
        if form_label:
            return f"*Main Menu*\n\n• {form_label}\n\nType '{form_label}' to continue!"

    # No menu to show - return None
    return None

def _get_contact_info(bot_settings, contact_data, phone=None, name=None):
    """Get contact info template with lead capture for interested users."""
    from models import Lead
    from database import SessionLocal

    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    enabled = templates.get("template_contact_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_contact")
    sn = contact_data.get('site_name') or "our business"

    # Build contact response
    if custom:
        response = custom.replace("{user_name}", name or "there").replace("{site_name}", sn).replace("{phone}", contact_data.get('phone') or 'N/A').replace("{email}", contact_data.get('email') or 'N/A').replace("{address}", contact_data.get('address') or 'N/A')
    else:
        # No custom template - return None
        return None

    # Add conversational follow-up to capture lead
    if phone:
        # Capture lead with high interest when they ask for contact
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.bot_id == bot_settings.get('_bot_id'), Lead.phone == phone).first()
            if lead:
                context = lead.context or {}
                context["interest_level"] = "high"
                context["requested_contact"] = True
                lead.context = context
                flag_modified(lead, 'context')
                lead.name = name or lead.name
                db.commit()
                logger.info(f"🎯 Lead marked as highly interested (requested contact): {phone}")
        except Exception as e:
            logger.error(f"Error updating lead interest: {e}")
            db.rollback()
        finally:
            db.close()

    return response

def _get_delivery_info(bot_settings):
    """Get delivery info template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    enabled = templates.get("template_delivery_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_delivery")
    if custom:
        return custom

    # No default fallback
    return None

def _get_services(bot_settings):
    """Get services template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    enabled = templates.get("template_services_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_services")
    if custom:
        return custom

    # No default fallback
    return None


def _get_product_text(bot_settings):
    """Get product text template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    # Check if product template is enabled (Issue 1)
    enabled = templates.get("template_product_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_product")
    if custom:
        return custom

    # No default fallback
    return None


def _get_order_form(bot_settings):
    """Get order form template from bot settings."""
    # Check if order form is enabled
    order_form_enabled = bot_settings.get("order_form_enabled", True)
    if not order_form_enabled:
        return None

    # Get custom order form template
    custom_template = bot_settings.get("order_form_template")
    if custom_template:
        return custom_template

    # No default fallback
    return None


def _get_order_confirmation_template(bot_settings, order_data=None):
    """Get order confirmation message from bot settings."""
    # Get custom confirmation message
    custom_confirmation = bot_settings.get("order_confirmation_message")
    if custom_confirmation:
        return custom_confirmation

    # No default fallback
    return None

# ===================== LOGIC =====================

def _save_order(bot_id: int, user_id: int, phone: str, order_details: str):
    """Save order to database with raw filled form details."""
    from models import Order, Bot
    from database import SessionLocal
    from routers.notifications import create_notification

    db = SessionLocal()
    try:
        # Ensure user_id is valid - if None, get it from bot
        if user_id is None:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                user_id = bot.user_id
                logger.info(f"Retrieved user_id {user_id} from bot {bot_id}")
            else:
                logger.error(f"Cannot save order: bot {bot_id} not found")
                return False

        if user_id is None:
            logger.error(f"Cannot save order: user_id is None for bot {bot_id}")
            return False

        logger.info(f"💾 Saving order to database...")
        logger.info(f"💾 bot_id={bot_id}, user_id={user_id}, phone={phone}")
        logger.info(f"💾 order_details length: {len(order_details)} chars")
        logger.info(f"💾 order_details content: {order_details}")

        order = Order(
            bot_id=bot_id,
            user_id=user_id,
            phone=phone,
            order_details=order_details,  # Save raw filled form
            source="default_mode"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        logger.info(f"✅ Order saved successfully: Order ID {order.id} from {phone}")
        logger.info(f"✅ Saved order_details: {order.order_details}")

        # Create notification for new order
        try:
            create_notification(
                db=db,
                user_id=user_id,
                type="new_order",
                title="New Order Received",
                message=f"New order from {phone}"
            )
        except Exception as e:
            logger.error(f"Failed to create order notification: {e}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to save order: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def process(bot_id: int, text: str, phone: str, name: str, business_type: str = "product",
            user_plan: str = "starter", products: list = None, services: list = None,
            contact_info: dict = None, user_id: int = None, bot_settings: dict = None):
    from models import Lead, BotSettings, Integration
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Get lead for context
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        st = lead.context if lead and lead.context else {"step": "active"}
        tl = text.lower().strip()

        # 2. Fetch Bot Settings (only if not provided as parameter)
        if bot_settings is None:
            bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
            if bs:
                # FORCE REFRESH from database to get latest settings (bypass any cache)
                db.expire(bs)  # Expire the object to force reload
                db.refresh(bs)  # Reload from database

                # Merge template_statuses into templates so toggle states are accessible
                merged_templates = bs.templates or {}
                if bs.template_statuses:
                    merged_templates.update(bs.template_statuses)
                bot_settings = {
                    "templates": merged_templates,
                    "custom_responses": bs.custom_responses or {},
                    "language": bs.language or "english",
                    "order_form_template": bs.order_form_template,
                    "order_confirmation_message": bs.order_confirmation_message,
                    "order_form_enabled": bs.order_form_enabled if bs.order_form_enabled is not None else True,
                    "form_menu_label": bs.form_menu_label,
                    "fallback_message": bs.fallback_message,
                    "order_error_message": bs.order_error_message,
                    "error_message": bs.error_message,
                    "_bot_id": bot_id  # Store bot_id for lead capture
                }
            else:
                bot_settings = {
                    "templates": {},
                    "custom_responses": {},
                    "language": "english",
                    "order_form_template": None,
                    "order_confirmation_message": None,
                    "order_form_enabled": True,
                    "fallback_message": None,
                    "order_error_message": None,
                    "error_message": None,
                    "_bot_id": bot_id
                }

        # 3. Handle Context Data - Use passed-in contact_info (already fetched from user's integration)
        contact_data = {
            "site_name": contact_info.get("site_name") or "our business",
            "phone": contact_info.get("phone") or "N/A",
            "email": contact_info.get("email") or "N/A",
            "address": contact_info.get("address") or "N/A",
            "services": contact_info.get("services") or [],
            "about": contact_info.get("about") or "",
        }

        # Fallback: If phone still N/A, try to get WhatsApp number from integration
        if contact_data["phone"] == "N/A":
            integ = db.query(Integration).filter(Integration.bot_id == bot_id).first()
            if integ and integ.whatsapp_number:
                contact_data["phone"] = integ.whatsapp_number

        # 4. EXIT HANDLER - Global keyword check (Issue 6)
        # Handle "exit" or "exist" (typo) to reset flow
        if tl in ["exit", "exist"]:
            # Reset state to active
            st = {"step": "active"}
            if lead:
                lead.context = st
                flag_modified(lead, 'context')
                db.commit()

            # Return greeting if enabled, otherwise return to menu
            site_name = contact_data["site_name"]
            greeting = _get_greeting(name, site_name, bot_settings)
            if greeting:
                return greeting

            menu = _get_menu(business_type, bot_settings, site_name, user_id)
            if menu:
                return menu
            return ""

        # 5. Routing Logic
        site_name = contact_data["site_name"]

        # Handle greeting and menu FIRST (before any flow checks)
        if tl in ["menu", "start", "hi", "hello"]:
            st = {"step": "active"}
            if lead:
                lead.context = st
                flag_modified(lead, 'context')
            db.commit()

            if tl in ["hi", "hello"]:
                resp = _get_greeting(name, site_name, bot_settings)
                if resp:
                    menu = _get_menu(business_type, bot_settings, site_name, user_id)
                    if menu:
                        return resp + "\n\n" + menu
                    return resp
                # No greeting configured, show menu
                menu = _get_menu(business_type, bot_settings, site_name, user_id)
                if menu:
                    return menu
                return ""

            menu = _get_menu(business_type, bot_settings, site_name, user_id)
            if menu:
                return menu
            return ""

        # Check for order trigger - ONLY use custom form menu label (no hardcoded triggers)
        custom_label = bot_settings.get("form_menu_label")
        is_order_trigger = False

        if custom_label and custom_label.strip():
            # Exact match only - user must type the exact label
            is_order_trigger = (tl == custom_label.lower().strip())

        # Handle order flow - single form submission
        if st.get("step") == "ordering":
            # Customer has replied with filled form - save it as-is
            order_details = text.strip()

            logger.info(f"📦 ORDER RECEIVED from {phone}")
            logger.info(f"📦 Order details text length: {len(order_details)} characters")
            logger.info(f"📦 Order details preview: {order_details[:200]}...")

            # Save the order with raw details
            success = _save_order(
                bot_id=bot_id,
                user_id=user_id,
                phone=phone,
                order_details=order_details
            )

            # Reset state
            st = {"step": "active"}
            if lead:
                lead.context = st
                flag_modified(lead, 'context')
            db.commit()

            if success:
                # Get order confirmation message
                confirmation = _get_order_confirmation_template(bot_settings)
                if confirmation:
                    return confirmation
                # No custom confirmation - return empty
                return ""
            else:
                # Get custom error message
                error_message = bot_settings.get("order_error_message")
                if error_message:
                    return error_message
                # No custom error message - return empty
                return ""

        # Start order flow
        if is_order_trigger:
            # Check if order form is enabled
            order_enabled = bot_settings.get("order_form_enabled", True)

            if order_enabled:
                st = {"step": "ordering", "order_data": {}}
                if lead:
                    lead.context = st
                    flag_modified(lead, 'context')
                db.commit()
                return _get_order_form(bot_settings)
            else:
                # Order form disabled, show menu instead
                menu = _get_menu(business_type, bot_settings, site_name, user_id)
                if menu:
                    return menu
                return ""

        if st.get("step") == "active":
            # First, check if user input matches a custom template name
            from models import UserTemplate
            if user_id:
                try:
                    custom_templates = db.query(UserTemplate).filter(
                        UserTemplate.user_id == user_id
                    ).all()

                    # Try to match template name (case-insensitive)
                    for template in custom_templates:
                        if template.template_name.lower() == tl:
                            return template.content
                except Exception as e:
                    logger.error(f"Error matching custom template: {e}")

            # Check if user typed the custom order form label (same logic as templates)
            custom_label = bot_settings.get("form_menu_label")
            if custom_label and custom_label.lower() == tl:
                order_enabled = bot_settings.get("order_form_enabled", True)
                if order_enabled:
                    st = {"step": "ordering", "order_data": {}}
                    if lead:
                        lead.context = st
                        flag_modified(lead, 'context')
                    db.commit()
                    return _get_order_form(bot_settings)

            # If input is just a number, show error and menu
            if tl.isdigit():
                menu = _get_menu(business_type, bot_settings, site_name, user_id)
                if menu:
                    return menu
                # No hardcoded fallback - return empty to let bot_engine handle it
                return ""

            # If no match found, return empty to let bot_engine handle fallback
            return ""

        # Final fallback - show menu
        menu = _get_menu(business_type, bot_settings, site_name, user_id)
        if menu:
            return menu

        # If menu is disabled, check for custom fallback
        fallback_message = bot_settings.get("fallback_message")
        if fallback_message:
            return fallback_message.replace("{user_name}", name or "Customer")

        return ""

    except Exception as e:
        logger.error(f"Critical error in process(): {e}", exc_info=True)
        # Check for custom error message
        if bot_settings:
            error_message = bot_settings.get("error_message")
            if error_message:
                return error_message
        return ""
    finally:
        db.close()