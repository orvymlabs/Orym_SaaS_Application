"""
Default Bot Engine — Simplified English Logic (No Product Features)
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

# Global In-Memory Cache for Bot Settings (Simple but effective for single-process)
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
    return f"👋 Hi {name or 'there'}! Welcome to {sn}. Type *menu* to see how I can help you today!"

def _get_menu(business_type, bot_settings, site_name):
    """Get menu template with dynamic numbered options."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
    
    enabled = templates.get("template_menu_enabled", True)
    if not enabled:
        return None
        
    custom = templates.get("template_menu")
    if custom:
        return custom

    # Default enabled states
    enabled_map = {
        "services": business_type == "service",
        "delivery": True,
        "contact": True
    }

    # Check customized flags
    for key in ["delivery", "contact", "services"]:
        val = templates.get(f"template_{key}_enabled")
        if val is not None:
            enabled_map[key] = val

    # Build dynamic menu with numbered options
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

    if not menu_items:
        return "Our bot is currently being updated. Please check back later!"

    items_str = "\n".join(menu_items)
    return f"📋 *Main Menu*\n\n{items_str}\n\n💬 Reply with a number to continue!"

def _get_contact_info(bot_settings, contact_data):
    """Get contact info template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
    
    enabled = templates.get("template_contact_enabled", True)
    if not enabled:
        return None
        
    custom = templates.get("template_contact")
    sn = contact_data.get('site_name') or "our business"
    
    if custom:
        return custom.replace("{site_name}", sn).replace("{phone}", contact_data.get('phone') or 'N/A').replace("{email}", contact_data.get('email') or 'N/A').replace("{address}", contact_data.get('address') or 'N/A')

    return f"📞 *Contact Us*\n\n🏢 {sn}\n📱 {contact_data.get('phone', 'N/A')}\n📧 {contact_data.get('email', 'N/A')}\n📍 {contact_data.get('address', 'N/A')}"

def _get_delivery_info(bot_settings):
    """Get delivery info template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
    
    enabled = templates.get("template_delivery_enabled", True)
    if not enabled:
        return None
        
    custom = templates.get("template_delivery")
    if custom:
        return custom

    return "🚚 *Delivery Information*\n\nWe offer fast nationwide delivery within 3-5 business days."

def _get_services(bot_settings):
    """Get services template."""
    templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
    
    enabled = templates.get("template_services_enabled", True)
    if not enabled:
        return None
        
    custom = templates.get("template_services")
    if custom:
        return custom

    return "🏭 *Our Services*\n\nPlease visit our website or contact us to learn more about our professional services."

# ===================== LOGIC =====================

def process(bot_id: int, text: str, phone: str, name: str, business_type: str = "product", 
            user_plan: str = "starter", products: list = None, services: list = None, 
            contact_info: dict = None):
    from models import Lead, BotSettings, Integration
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # 1. Fetch/Update Lead
        lead = db.query(Lead).filter(Lead.bot_id == bot_id, Lead.phone == phone).first()
        if not lead:
            lead = Lead(bot_id=bot_id, phone=phone, name=name, context={"step": "active"})
            db.add(lead)
            db.commit()
            db.refresh(lead)
        
        st = lead.context or {"step": "active"}
        tl = text.lower().strip()
        
        # 2. Fetch Bot Settings (with caching)
        with _cache_lock:
            if bot_id not in _bot_settings_cache:
                bs = db.query(BotSettings).filter(BotSettings.bot_id == bot_id).first()
                if bs:
                    # Explicitly refresh from DB to ensure no ORM caching
                    db.refresh(bs)
                    _bot_settings_cache[bot_id] = {
                        "templates": bs.templates or {},
                        "custom_responses": bs.custom_responses or {},
                        "language": bs.language or "english"
                    }
                else:
                    _bot_settings_cache[bot_id] = {"templates": {}, "custom_responses": {}, "language": "english"}
            
            bot_settings = _bot_settings_cache[bot_id]

        # 3. Handle Context Data
        integ = db.query(Integration).filter(Integration.bot_id == bot_id).first()
        site_name = contact_info.get("site_name") if contact_info else "our business"
        if not site_name or site_name == "our business":
            if integ and integ.woocommerce_url:
                site_name = integ.woocommerce_url.replace("https://", "").replace("http://", "").split("/")[0]

        contact_data = {
            "site_name": site_name,
            "phone": contact_info.get("phone") if contact_info else "N/A",
            "email": contact_info.get("email") if contact_info else "N/A",
            "address": contact_info.get("address") if contact_info else "N/A"
        }
        if integ and contact_data["phone"] == "N/A": 
            contact_data["phone"] = integ.whatsapp_number or "N/A"

        # 4. Routing Logic
        if tl in ["menu", "0", "start", "hi", "hello"]:
            st = {"step": "active"}
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
        
        if st.get("step") == "active":
            # Map numbers to actions
            templates = bot_settings.get("templates") or bot_settings.get("custom_responses") or {}
            enabled_map = {
                "services": business_type == "service",
                "delivery": True,
                "contact": True
            }
            for key in ["delivery", "contact", "services"]:
                val = templates.get(f"template_{key}_enabled")
                if val is not None: enabled_map[key] = val

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

            if tl in menu_map:
                option = menu_map[tl]
                if option == "services": return _get_services(bot_settings)
                if option == "delivery": return _get_delivery_info(bot_settings)
                if option == "contact": return _get_contact_info(bot_settings, contact_data)

            # Keyword triggers
            if tl in ["delivery", "shipping"]: return _get_delivery_info(bot_settings)
            if tl in ["contact", "reach"]: return _get_contact_info(bot_settings, contact_data)
            if tl in ["services", "service"]: return _get_services(bot_settings)

            return "❓ I didn't quite catch that. Type *menu* to see available options."

        return _get_menu(business_type, bot_settings, site_name)
        
    except Exception as e:
        logger.error(f"Critical error in process(): {e}", exc_info=True)
        return "I'm sorry, I'm having some technical trouble. Please try again in a few minutes."
    finally:
        db.close()
