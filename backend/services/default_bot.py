"""
Default Bot Engine — Simplified English Logic
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

PRODUCT_LIMIT_WARNING = "📦 *Starter Plan Limit*: Showing first 10 products. Upgrade to Growth for unlimited products."

# ===================== UI HELPERS =====================

def _get_greeting(user_name, site_name, business_type, bot_id=None, db=None, lang="english"):
    """Get greeting template - falls back to default if not customized."""
    custom = None
    enabled = True
    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_greeting_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_greeting")

    if custom:
        return custom.replace("{user_name}", user_name or "there").replace("{site_name}", site_name or "our business")

    if not enabled: return None
    # Default greeting with menu hint
    sn = site_name or "our business"
    return f"👋 Hi {user_name or 'there'}! Welcome to {sn}. Type *menu* to see how I can help you today!"

def _get_menu(business_type, bot_id=None, db=None, lang="english", contact_info=None, products=None, services=None):
    """Get menu template with dynamic numbered options based on enabled status and business type."""
    custom = None
    enabled = True
    # Default enabled states - services only for service business type
    enabled_map = {
        "services": business_type == "service",
        "order": business_type == "product",
        "product_list": business_type == "product",
        "delivery": True,
        "contact": True
    }

    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_menu_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_menu")

            # Check disabled flags for each section
            for key in ["order", "product_list", "delivery", "contact", "services"]:
                val = data_source.get(f"template_{key}_enabled")
                if val is not None:
                    enabled_map[key] = val

    if custom:
        return custom

    if not enabled:
        return None

    # Build dynamic menu with numbered options
    menu_items = []
    num = 1
    # Order of options: services, order, product_list, delivery, contact
    if enabled_map.get("services"):
        menu_items.append(f"{num}. Services")
        num += 1
    if enabled_map.get("order"):
        menu_items.append(f"{num}. Order Products")
        num += 1
    if enabled_map.get("product_list"):
        menu_items.append(f"{num}. Product Catalog")
        num += 1
    if enabled_map.get("delivery"):
        menu_items.append(f"{num}. Delivery Info")
        num += 1
    if enabled_map.get("contact"):
        menu_items.append(f"{num}. Contact Us")
        num += 1

    if not menu_items:
        return "Our bot is currently being updated. Please check back later!"

    items_str = "\n".join(menu_items)
    return f"📋 *Main Menu*\n\n{items_str}\n\n💬 Reply with a number to continue!"

def _get_contact_info(contact, bot_id=None, db=None, lang="english"):
    """Get contact info template - only custom content, no hardcoded default."""
    custom = None
    enabled = True
    c = contact or {}
    sn = c.get('site_name') or "our business"

    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_contact_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_contact")

    if custom:
        return custom.replace("{site_name}", sn).replace("{phone}", c.get('phone') or 'N/A').replace("{email}", c.get('email') or 'N/A').replace("{address}", c.get('address') or 'N/A')

    if not enabled: return None
    # No default - return None to skip
    return None

def _get_delivery_info(bot_id=None, db=None, lang="english"):
    """Get delivery info template - only custom content, no hardcoded default."""
    custom = None
    enabled = True

    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_delivery_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_delivery")

    if custom:
        return custom

    if not enabled: return None
    # No default - return None to skip
    return None

def _get_services(services, lang="english", bot_id=None, db=None):
    """Get services template - only custom content, no hardcoded default."""
    custom = None
    enabled = True

    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_services_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_services")

    if custom:
        return custom

    if not enabled: return None
    # No default - return None to skip
    return None
def _t_all_products(items, total, bot_id=None, db=None, lang="english"):
    """Get product list template - only custom content, no hardcoded default."""
    custom = None
    enabled = True

    if bot_id and db:
        from models import BotSettings
        bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
        if bs:
            data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
            if not data_source: data_source = {}

            lang = bs.language or lang
            enabled = data_source.get("template_product_list_enabled", True)
            if not enabled:
                return None
            custom = data_source.get(f"template_product_list")

    item_list = "\n".join(items[:10]) if items else "No products available."

    if custom:
        return custom.replace("{total}", str(total)).replace("{item_list}", item_list)

    if not enabled: return None
    # No default - return None to skip
    return None

def _t_order_confirm(product_name, qty, user_name, address, phone, contact):
    return f"✅ *Order Confirmed!*\n📦 Product: {product_name}\n🔢 Quantity: {qty}\n👤 Name: {user_name}\n📍 Address: {address}\n📱 Phone: {phone}\n\n🚚 We will contact you soon!"

def _search_products(text, products):
    matches = [f"• {p.get('name')} - {p.get('price', 'Contact')}" for p in products if text.lower() in p.get('name', '').lower()]
    if not matches: return None
    item_list = "\n".join(matches[:10])
    return f"🔍 *Search Results* ({len(matches)}):\n\n{item_list}\n\n💬 Type *order* to buy!"

# ===================== LOGIC =====================

def get_custom_response(bot_id: int, key: str, default_val: str, db: Session) -> str:
    from models import BotSettings
    bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
    if not bs: return default_val
    # Priority: templates column, then custom_responses fallback
    data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
    if not data_source: return default_val
    return data_source.get(key, default_val)

def process(bot_id: int, text: str, phone: str, name: str, business_type: str = "product", 
            user_plan: str = "starter", products: list = None, services: list = None, 
            contact_info: dict = None):
    from models import Lead, BotSettings, Integration
    from database import SessionLocal
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        if not lead:
            lead = Lead(bot_id=bot_id, phone=phone, name=name, context={"step": "active"})
            db.add(lead)
            db.commit()
            db.refresh(lead)
        st = lead.context or {"step": "active"}
        tl = text.lower().strip()
        
        # Safely fetch integration data
        integ = db.query(Integration).filter(Integration.bot_id == bot_id).first()
        
        # Initialize context data with passed arguments or defaults
        products = products or []
        services = services or (contact_info.get("services") if contact_info else [])
        
        site_name = "our business"
        if contact_info and contact_info.get("site_name"):
            site_name = contact_info["site_name"]
        elif integ and integ.woocommerce_url:
            site_name = integ.woocommerce_url.replace("https://", "").replace("http://", "").split("/")[0]

        contact_data = {
            "site_name": site_name,
            "phone": contact_info.get("phone") if contact_info else "N/A",
            "email": contact_info.get("email") if contact_info else "N/A",
            "address": contact_info.get("address") if contact_info else "N/A",
            "hours": contact_info.get("hours") if contact_info else ""
        }

        # Fallback to integration data if contact_info is sparse
        if integ:
            if contact_data["phone"] == "N/A": contact_data["phone"] = integ.whatsapp_number or "N/A"

        if tl in ["menu", "0", "start", "hi", "hello"]:
            st = {"step": "active"}
            lead.context = st
            db.commit()

            resp = None
            if tl in ["hi", "hello"]:
                resp = _get_greeting(name, site_name, business_type, bot_id, db)
                # After greeting, also show menu
                if resp:
                    menu = _get_menu(business_type, bot_id, db, contact_info=contact_data, products=products, services=services)
                    if menu:
                        resp = resp + "\n\n" + menu
            else:
                resp = _get_menu(business_type, bot_id, db, contact_info=contact_data, products=products, services=services)

            return resp if resp else "Type *menu* to see available options."
        
        if st.get("step") == "active":
            # Build menu mapping based on enabled options (same logic as _get_menu)
            enabled_map = {
                "services": business_type == "service",
                "order": business_type == "product",
                "product_list": business_type == "product",
                "delivery": True,
                "contact": True
            }
            # Check template settings for enabled/disabled
            bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
            if bs:
                data_source = bs.templates if (hasattr(bs, 'templates') and bs.templates) else bs.custom_responses
                if data_source:
                    for key in ["order", "product_list", "delivery", "contact", "services"]:
                        val = data_source.get(f"template_{key}_enabled")
                        if val is not None:
                            enabled_map[key] = val

            menu_map = {}
            num = 1
            if enabled_map.get("services"):
                menu_map[str(num)] = "services"
                num += 1
            if enabled_map.get("order"):
                menu_map[str(num)] = "order"
                num += 1
            if enabled_map.get("product_list"):
                menu_map[str(num)] = "product_list"
                num += 1
            if enabled_map.get("delivery"):
                menu_map[str(num)] = "delivery"
                num += 1
            if enabled_map.get("contact"):
                menu_map[str(num)] = "contact"
                num += 1

            resp = None
            # Check if user typed a number matching menu option
            if tl in menu_map:
                option = menu_map[tl]
                if option == "order":
                    st["step"] = "sales_product"
                    lead.context = st
                    db.commit()
                    return "🛍️ Which product would you like to order?"
                elif option == "services":
                    resp = _get_services(services, "english", bot_id, db)
                elif option == "product_list":
                    items = [f"• {p.get('name')} - {p.get('price', 'Contact')}" for p in products]
                    resp = _t_all_products(items, len(products), bot_id, db)
                elif option == "delivery":
                    resp = _get_delivery_info(bot_id, db)
                elif option == "contact":
                    resp = _get_contact_info(contact_data, bot_id, db)
            elif tl in ["order"]:
                st["step"] = "sales_product"
                lead.context = st
                db.commit()
                return "🛍️ Which product would you like to order?"
            elif tl in ["inquiry", "products", "catalog"]:
                items = [f"• {p.get('name')} - {p.get('price', 'Contact')}" for p in products]
                resp = _t_all_products(items, len(products), bot_id, db)
            elif tl in ["delivery", "about", "shipping"]:
                resp = _get_delivery_info(bot_id, db)
            elif tl in ["contact", "reach"]:
                resp = _get_contact_info(contact_data, bot_id, db)
            elif tl in ["services", "service"]:
                resp = _get_services(services, "english", bot_id, db)

            if resp: return resp

            # If no template triggered, try product search
            search_res = _search_products(text, products)
            if search_res: return search_res

            return "❓ I didn't quite catch that. Type *menu* to see available options."

        if st.get("step") == "sales_product":
            st.update({"order_product": text, "step": "sales_quantity"})
            lead.context = st
            db.commit()
            return "🔢 How many pieces would you like to order?"
        
        if st.get("step") == "sales_quantity":
            st.update({"order_qty": text, "step": "sales_details"})
            lead.context = st
            db.commit()
            return "👤 Please provide your Full Name and Delivery Address."

        if st.get("step") == "sales_details":
            st.update({"order_address": text, "step": "sales_confirm"})
            lead.context = st
            db.commit()
            return f"📝 *Order Summary*\nProduct: {st.get('order_product')}\nQty: {st.get('order_qty')}\nAddress: {text}\n\nType *yes* to confirm this order."
            
        if st.get("step") == "sales_confirm":
            if tl == "yes":
                msg = _t_order_confirm(st.get("order_product"), st.get("order_qty"), name, st.get("order_address"), phone, contact_data)
                st = {"step": "active"}
                lead.context = st
                db.commit()
                return msg
            st = {"step": "active"}
            lead.context = st
            db.commit()
            return "❌ Order has been cancelled. Type *menu* to start over."

        return _get_menu(business_type, bot_id, db)
    except Exception as e:
        logger.error(f"Critical error in process(): {e}", exc_info=True)
        return "I'm sorry, I'm having some technical trouble. Please try again in a few minutes."
    finally:
        db.close()
