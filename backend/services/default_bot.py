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

    # Default fallback
    sn = site_name or "our business"
    return f"Hi {name or 'there'}! Welcome to {sn}. Type *menu* to see how I can help you today!"

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
                if order_form_enabled:
                    menu_items.append("• Order")

                items_str = "\n".join(menu_items)
                return f"*Main Menu*\n\n{items_str}\n\nType the name of any option to continue!"
        except Exception as e:
            logger.error(f"Error fetching custom templates: {e}")
        finally:
            db.close()

    # Fallback to legacy numbered menu if no custom templates
    enabled_map = {
        "services": templates.get("template_services_enabled", business_type == "service"),
        "delivery": templates.get("template_delivery_enabled", True),
        "contact": templates.get("template_contact_enabled", True),
        "product": templates.get("template_product_enabled", True),
        "order_form": templates.get("template_order_form_enabled", True)
    }

    # Build menu items dynamically
    menu_items = []
    num = 1
    if enabled_map.get("services"):
        menu_items.append(f"{num}. Services")
        num += 1
    if enabled_map.get("delivery"):
        menu_items.append(f"{num}. Delivery Info")
        num += 1
    if enabled_map.get("contact"):
        menu_items.append(f"{num}. Contact Us")
        num += 1
    if enabled_map.get("product"):
        menu_items.append(f"{num}. Products")
        num += 1
    if enabled_map.get("order_form"):
        menu_items.append(f"{num}. Place Order")
        num += 1

    if not menu_items:
        return "Our bot is currently being updated. Please check back later!"

    items_str = "\n".join(menu_items)
    return f"*Main Menu*\n\n{items_str}\n\nReply with a number to continue!"

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
        response = f"*Contact Us*\n\n{sn}\nPhone: {contact_data.get('phone', 'N/A')}\nEmail: {contact_data.get('email', 'N/A')}\nAddress: {contact_data.get('address', 'N/A')}"

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

    # Add conversational follow-up
    response += "\n\nWould you like us to call or email you? Just share your preferred contact method!"

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

    return "*Delivery Information*\n\nWe offer fast nationwide delivery within 3-5 business days."

def _get_services(bot_settings):
    """Get services template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    enabled = templates.get("template_services_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_services")
    if custom:
        return custom

    return "*Our Services*\n\nWe offer a wide range of services tailored to your needs.\nPlease visit our website or contact us to learn more about our professional services."


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

    return "*Our Products*\n\nWe sell high-quality shirts and apparel. Browse our collection and place your order!"


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

    # Default fallback
    return """🛍️ Order Form

Please fill in the details below and reply:

Full Name:
Phone Number:
Delivery Address:
Product / Item:
Quantity:
Special Instructions (optional):"""


def _get_order_confirmation_template(bot_settings, order_data=None):
    """Get order confirmation message from bot settings."""
    # Get custom confirmation message
    custom_confirmation = bot_settings.get("order_confirmation_message")
    if custom_confirmation:
        return custom_confirmation

    # Default fallback
    return """✅ Thank you! Your order has been received.
Our team will contact you shortly to confirm."""

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
                # FORCE REFRESH from database to get latest settings
                db.refresh(bs)
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
            else:
                menu = _get_menu(business_type, bot_settings, site_name, user_id)
                if menu:
                    return menu
                return "Returning to main menu..."

        # 5. Routing Logic
        site_name = contact_data["site_name"]

        # Handle greeting and menu FIRST (before any flow checks)
        if tl in ["menu", "0", "start", "hi", "hello"]:
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
                return resp or "Type *menu* to see options."

            return _get_menu(business_type, bot_settings, site_name, user_id) or "Type *menu* to see options."

        # Check for order trigger words
        order_triggers = ["order", "buy", "purchase", "i want to buy", "i want to order"]
        is_order_trigger = any(trigger in tl for trigger in order_triggers)

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
                else:
                    return "Order saved successfully!"
            else:
                return "Sorry, there was an error saving your order. Please try again or contact us directly."

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
                return _get_menu(business_type, bot_settings, site_name, user_id) or "Type *menu* to see options."

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

            # Check if user typed "order" and order form is enabled
            if tl == "order":
                order_enabled = bot_settings.get("order_form_enabled", True)
                if order_enabled:
                    st = {"step": "ordering", "order_data": {}}
                    if lead:
                        lead.context = st
                        flag_modified(lead, 'context')
                    db.commit()
                    return _get_order_form(bot_settings)

            # Map numbers to actions based on enabled templates
            templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
            enabled_map = {
                "services": templates.get("template_services_enabled", business_type == "service"),
                "delivery": templates.get("template_delivery_enabled", True),
                "contact": templates.get("template_contact_enabled", True),
                "product": templates.get("template_product_enabled", True),
                "order_form": templates.get("template_order_form_enabled", True)
            }

            # Build dynamic menu mapping
            menu_map = {}
            num = 1
            if enabled_map.get("services"):
                menu_map[str(num)] = "services"
                num += 1
            if enabled_map.get("delivery"):
                menu_map[str(num)] = "delivery"
                num += 1
            if enabled_map.get("contact"):
                menu_map[str(num)] = "contact"
                num += 1
            if enabled_map.get("product"):
                menu_map[str(num)] = "product"
                num += 1
            if enabled_map.get("order_form"):
                menu_map[str(num)] = "order"
                num += 1

            # Handle numbered menu selections
            if tl in menu_map:
                option = menu_map[tl]
                if option == "services":
                    resp = _get_services(bot_settings)
                    return resp if resp else "Services information is currently unavailable."
                if option == "delivery":
                    resp = _get_delivery_info(bot_settings)
                    return resp if resp else "Delivery information is currently unavailable."
                if option == "contact":
                    resp = _get_contact_info(bot_settings, contact_data, phone=phone, name=name)
                    return resp if resp else "Contact information is currently unavailable."
                if option == "product":
                    resp = _get_product_text(bot_settings)
                    return resp if resp else "Product information is currently unavailable."
                if option == "order":
                    # Start order flow
                    st = {"step": "ordering", "order_data": {}}
                    if lead:
                        lead.context = st
                        flag_modified(lead, 'context')
                    db.commit()
                    return _get_order_form(bot_settings)

            # Keyword triggers
            if tl in ["delivery", "shipping"]:
                resp = _get_delivery_info(bot_settings)
                return resp if resp else "Delivery information is currently unavailable."
            if tl in ["contact", "reach"]:
                resp = _get_contact_info(bot_settings, contact_data, phone=phone, name=name)
                return resp if resp else "Contact information is currently unavailable."
            if tl in ["services", "service"]:
                resp = _get_services(bot_settings)
                return resp if resp else "Services information is currently unavailable."
            if tl in ["product", "products", "shirt", "shirts"]:
                resp = _get_product_text(bot_settings)
                return resp if resp else "Product information is currently unavailable."

            # If no match found, show menu or fallback message
            menu = _get_menu(business_type, bot_settings, site_name, user_id)
            if menu:
                return "❓ I didn't quite catch that. Here's the menu:\n\n" + menu
            return "❓ I didn't quite catch that. Type *menu* to see available options."

        return _get_menu(business_type, bot_settings, site_name, user_id)
        
    except Exception as e:
        logger.error(f"Critical error in process(): {e}", exc_info=True)
        return "I'm sorry, I'm having some technical trouble. Please try again in a few minutes."
    finally:
        db.close()