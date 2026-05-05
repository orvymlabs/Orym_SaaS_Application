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

def _get_menu(business_type, bot_settings, site_name):
    """Get menu template with dynamic numbered options based on enabled templates."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    # Check if menu is enabled (Issue 1)
    enabled = templates.get("template_menu_enabled", True)
    if not enabled:
        return None

    # Check if there's a custom menu saved
    custom = templates.get("template_menu")
    if custom:
        return custom

    # Build dynamic menu with numbered options based on enabled templates
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
    """Get order form template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    # Check if order form is enabled (Issue 1)
    enabled = templates.get("template_order_form_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_order_form")
    if custom:
        return custom

    return """*Order Form*

Please provide your order details in the following format:

Name: [Your Full Name]
Product: [Product Name]
Quantity: [Number]
Address: [Delivery Address]
Phone: [Phone Number]

Example:
Name: John Doe
Product: Blue Shirt
Quantity: 2
Address: 123 Main Street, City
Phone: +1234567890"""


def _get_order_confirmation_template(bot_settings, order_data=None):
    """Get order confirmation template with placeholder replacement."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}

    # Check if order confirmation is enabled
    enabled = templates.get("template_order_confirmation_enabled", True)
    if not enabled:
        return None

    custom = templates.get("template_order_confirmation")

    # Replace placeholders if order_data is provided
    if custom and order_data:
        message = custom
        message = message.replace("{name}", order_data.get("name", "Customer"))
        message = message.replace("{product}", order_data.get("product_name", ""))
        message = message.replace("{quantity}", str(order_data.get("quantity", 1)))
        message = message.replace("{address}", order_data.get("address", ""))
        message = message.replace("{phone}", order_data.get("phone", ""))
        return message
    elif custom:
        return custom

    # Default fallback
    if order_data:
        return f"*Order Confirmed!*\n\nThank you {order_data.get('name', 'Customer')} for your order!\n\nProduct: {order_data.get('product_name', '')}\nQuantity: {order_data.get('quantity', 1)}\nDelivery to: {order_data.get('address', '')}\n\nWe'll contact you soon at {order_data.get('phone', '')} to confirm delivery details."

    return "*Order Confirmed!*\n\nThank you for your order! We'll contact you soon to confirm delivery details."

# ===================== LOGIC =====================

def _save_order(bot_id: int, user_id: int, phone: str, name: str, product_name: str, quantity: int, address: str):
    """Save order to database."""
    from models import Order, Bot
    from database import SessionLocal

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

        order = Order(
            bot_id=bot_id,
            user_id=user_id,
            name=name,
            phone=phone,
            product_name=product_name,
            quantity=quantity,
            address=address,
            source="default_mode"
        )
        db.add(order)
        db.commit()
        logger.info(f"📦 Order saved: {product_name} x{quantity} for {name} (Order ID: {order.id})")
        return True
    except Exception as e:
        logger.error(f"Failed to save order: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def process(bot_id: int, text: str, phone: str, name: str, business_type: str = "product",
            user_plan: str = "starter", products: list = None, services: list = None,
            contact_info: dict = None, user_id: int = None):
    from models import Lead, BotSettings, Integration
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Get lead for context
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        st = lead.context if lead and lead.context else {"step": "active"}
        tl = text.lower().strip()

        # 2. Fetch Bot Settings (always refresh from database to ensure latest settings)
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
                "_bot_id": bot_id  # Store bot_id for lead capture
            }
        else:
            bot_settings = {"templates": {}, "custom_responses": {}, "language": "english", "_bot_id": bot_id}

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
                db.commit()

            # Return greeting if enabled, otherwise return to menu
            site_name = contact_data["site_name"]
            greeting = _get_greeting(name, site_name, bot_settings)
            if greeting:
                return greeting
            else:
                menu = _get_menu(business_type, bot_settings, site_name)
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
            db.commit()

            if tl in ["hi", "hello"]:
                resp = _get_greeting(name, site_name, bot_settings)
                if resp:
                    menu = _get_menu(business_type, bot_settings, site_name)
                    if menu:
                        return resp + "\n\n" + menu
                return resp or "Type *menu* to see options."

            return _get_menu(business_type, bot_settings, site_name) or "Type *menu* to see options."

        # Check for order trigger words
        order_triggers = ["order", "buy", "purchase", "i want to buy", "i want to order"]
        is_order_trigger = any(trigger in tl for trigger in order_triggers)

        # Handle order flow - single form submission
        if st.get("step") == "ordering":
            # Parse the order information from user's message
            order_data = {}
            lines = text.strip().split('\n')

            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if 'name' in key:
                        order_data['name'] = value
                    elif 'product' in key:
                        order_data['product_name'] = value
                    elif 'quantity' in key or 'qty' in key:
                        try:
                            order_data['quantity'] = int(value)
                        except ValueError:
                            order_data['quantity'] = 1
                    elif 'address' in key:
                        order_data['address'] = value
                    elif 'phone' in key:
                        order_data['phone'] = value

            # Validate required fields
            required_fields = ['name', 'product_name', 'quantity', 'address', 'phone']
            missing_fields = [f for f in required_fields if f not in order_data or not order_data[f]]

            if missing_fields:
                # Show which fields are missing
                missing_names = []
                for f in missing_fields:
                    if f == 'product_name':
                        missing_names.append('Product')
                    elif f == 'quantity':
                        missing_names.append('Quantity')
                    else:
                        missing_names.append(f.capitalize())

                return f"Please provide all required information. Missing: {', '.join(missing_names)}\n\nPlease use the format:\nName: [Your Name]\nProduct: [Product]\nQuantity: [Number]\nAddress: [Address]\nPhone: [Phone]"

            # Save the order
            success = _save_order(
                bot_id=bot_id,
                user_id=user_id,
                phone=order_data['phone'],
                name=order_data['name'],
                product_name=order_data['product_name'],
                quantity=order_data['quantity'],
                address=order_data['address']
            )

            # Reset state
            st = {"step": "active"}
            if lead:
                lead.context = st
            db.commit()

            if success:
                # Get order confirmation with placeholders replaced
                confirmation = _get_order_confirmation_template(bot_settings, order_data)
                if confirmation:
                    return confirmation
                else:
                    # If confirmation template is disabled, just save silently
                    return "Order saved successfully!"
            else:
                return "Sorry, there was an error saving your order. Please try again or contact us directly."

        # Start order flow
        if is_order_trigger:
            # Check if order form is enabled in templates (Issue 1)
            templates = bot_settings.get("templates") or {}
            order_enabled = templates.get("template_order_form_enabled", True)

            if order_enabled:
                st = {"step": "ordering", "order_data": {}}
                if lead:
                    lead.context = st
                db.commit()
                return _get_order_form(bot_settings)
            else:
                # Order form disabled, show menu instead
                return _get_menu(business_type, bot_settings, site_name) or "Type *menu* to see options."

        if st.get("step") == "active":
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

            return "❓ I didn't quite catch that. Type *menu* to see available options."

        return _get_menu(business_type, bot_settings, site_name)
        
    except Exception as e:
        logger.error(f"Critical error in process(): {e}", exc_info=True)
        return "I'm sorry, I'm having some technical trouble. Please try again in a few minutes."
    finally:
        db.close()