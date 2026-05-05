from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Bot, BotSettings, Integration, Message, Lead, User 
from schemas.bot import (
    BotResponse, BotSettingsUpdate, BotModeUpdate, BotStatusUpdate, SettingsResponse,
    TestChatRequest, TestChatResponse
)
from typing import Dict, List, Optional
from services import decode_token
from services.encryption import encrypt_value, decrypt_value
from services.bot_engine import handle_message
from services.ai_service import AVAILABLE_MODELS
from config import get_settings as get_app_settings
from pydantic import BaseModel
import logging
import json 

from services.universal_website_fetcher import UniversalWebsiteFetcher
from services.default_bot import clear_cache_for_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["bots"])

def get_plan_limits(plan: str) -> dict:
    if plan == "growth":
        return {"custom_responses": -1, "custom_products": -1}
    return {"custom_responses": 10, "custom_products": 20}

def get_user_plan(user_id: int, db: Session) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.plan if user else "starter"

def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return int(payload.get("sub", 0))

@router.get("/me", response_model=BotResponse)
def get_my_bot(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    return bot

@router.get("/ai/models")
def get_ai_models():
    return AVAILABLE_MODELS

# Default Mode Templates
DEFAULT_TEMPLATES = {
    "greeting": {
        "id": "greeting",
        "name": "Welcome Greeting",
        "logic": "The first message a user sees.",
        "placeholder": "Hi {user_name}! Welcome to {site_name}. Type *menu* to see how I can help you today!",
        "enabled": True
    },
    "menu": {
        "id": "menu",
        "name": "Main Menu",
        "logic": "The navigation hub.",
        "placeholder": "*Main Menu*\n\n1. Services\n2. Delivery Info\n3. Contact Us\n4. Products\n\nReply with a number to continue!",
        "enabled": True
    },
    "services": {
        "id": "services",
        "name": "Services Information",
        "logic": "Explains services offered.",
        "placeholder": "*Our Services*\n\nOur services include:\n• Web Development\n• Mobile Apps\n• UI/UX Design",
        "enabled": True
    },
    "delivery": {
        "id": "delivery",
        "name": "Delivery Information",
        "logic": "Explains shipping times.",
        "placeholder": "*Delivery Information*\n\nWe offer fast nationwide delivery within 3-5 business days.",
        "enabled": True
    },
    "contact": {
        "id": "contact",
        "name": "Contact Details",
        "logic": "Shows business info.",
        "placeholder": "*Contact Us*\n\n{site_name}\nPhone: {phone}\nEmail: {email}\nAddress: {address}",
        "enabled": True
    },
    "product": {
        "id": "product",
        "name": "Product Text",
        "logic": "Description of products for sale.",
        "placeholder": "*Our Products*\n\nWe sell high-quality shirts and apparel. Browse our collection and place your order!",
        "enabled": True
    },
    "order_confirmation": {
        "id": "order_confirmation",
        "name": "Order Confirmation",
        "logic": "Confirmation message after order is placed.",
        "placeholder": "*Order Confirmed!*\n\nThank you for your order! We'll contact you soon to confirm delivery details.",
        "enabled": True
    }
}

@router.get("/templates")
def get_automation_templates():
    return {"system_flow": list(DEFAULT_TEMPLATES.values())}

@router.get("/user-templates")
def get_user_templates(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")
    s = bot.settings
    user_templates = s.templates or s.custom_responses or {}
    result = []
    for template_id, default_template in DEFAULT_TEMPLATES.items():
        user_content = user_templates.get(f"template_{template_id}")
        user_enabled = user_templates.get(f"template_{template_id}_enabled", default_template["enabled"])
        result.append({
            "id": template_id,
            "name": default_template["name"],
            "logic": default_template["logic"],
            "placeholder": default_template["placeholder"],
            "content": user_content if user_content else default_template["placeholder"],
            "enabled": user_enabled if isinstance(user_enabled, bool) else True,
            "is_customized": user_content is not None,
            "type": "system"
        })
    return {"templates": result}

@router.patch("/mode")
def update_mode(data: BotModeUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    bot.mode = data.mode
    db.commit()
    clear_cache_for_bot(bot.id)
    return bot

@router.patch("/status")
def update_status(data: BotStatusUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    bot.status = data.status
    db.commit()
    clear_cache_for_bot(bot.id)
    return {"status": "ok", "bot_status": bot.status}

@router.get("/settings", response_model=SettingsResponse)
def get_settings(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")
    s = bot.settings
    # Return templates, custom_responses, and template_statuses
    return {
        "id": s.id,
        "bot_id": s.bot_id,
        "prompt": s.prompt,
        "model_name": s.model_name,
        "specific_model_name": s.specific_model_name,
        "temperature": s.temperature,
        "language": s.language,
        "templates": s.templates or {},
        "template_enabled": getattr(s, 'template_enabled', False),
        "template_statuses": s.template_statuses or {},
        "custom_responses": s.custom_responses or {},
        "custom_products": s.custom_products,
        "has_api_key": bool(s.api_key),
    }

@router.patch("/settings")
def update_settings(data: BotSettingsUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")
    s = bot.settings
    if data.prompt is not None: s.prompt = data.prompt
    if data.model_name is not None: s.model_name = data.model_name
    if data.specific_model_name is not None: s.specific_model_name = data.specific_model_name
    if data.api_key is not None: s.api_key = encrypt_value(data.api_key)
    if data.temperature is not None: s.temperature = data.temperature
    if data.language is not None: s.language = data.language
    if data.templates is not None:
        s.templates = data.templates
        # Log size of templates if available
        if data.templates and isinstance(data.templates, dict):
            # Estimate size by converting to JSON string and getting bytes
            templates_size = len(json.dumps(data.templates, ensure_ascii=False).encode('utf-8'))
            logger.debug(f"Received templates payload size: {templates_size} bytes")
        elif data.templates:
            logger.debug(f"Received templates payload (non-dict): {data.templates}")

    # Update custom_responses if provided (can be empty dict to clear rules)
    if data.custom_responses is not None:
        s.custom_responses = data.custom_responses
        # Log size of custom_responses if available
        if data.custom_responses and isinstance(data.custom_responses, dict):
            custom_responses_size = len(json.dumps(data.custom_responses, ensure_ascii=False).encode('utf-8'))
            logger.debug(f"Received custom_responses payload size: {custom_responses_size} bytes")
        elif data.custom_responses:
            logger.debug(f"Received custom_responses payload (non-dict): {data.custom_responses}")
        logger.info(f"Updated custom_responses: {data.custom_responses}")
    if data.template_enabled is not None: s.template_enabled = data.template_enabled

    # Save template_statuses (Issue 7 - CLAUDE.md)
    if data.template_statuses is not None:
        s.template_statuses = data.template_statuses
        logger.info(f"Updated template_statuses: {data.template_statuses}")

    # Measure commit time
    import time
    commit_start_time = time.time()
    db.commit()
    commit_end_time = time.time()
    commit_duration = commit_end_time - commit_start_time
    logger.info(f"Settings saved for bot {bot.id} after commit took {commit_duration:.4f} seconds.")

    clear_cache_for_bot(bot.id)

    return {"status": "ok"}

@router.post("/settings/uploadjson")
async def upload_json_settings(request: Request, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")
    try:
        data = await request.json()
        
        new_custom_responses = bot.settings.custom_responses or {}
        new_templates = bot.settings.templates or {}
        
        # Populate from explicit custom_responses in data
        if isinstance(data.get("custom_responses"), dict):
            new_custom_responses.update(data["custom_responses"])
        elif isinstance(data.get("custom_responses"), list):
            for item in data["custom_responses"]:
                if isinstance(item, dict) and "keyword" in item and "response" in item:
                    new_custom_responses[item["keyword"].lower()] = item["response"]
        
        # Populate from explicit templates in data
        if isinstance(data.get("templates"), dict):
            new_templates.update(data["templates"])
            
        # Fallback logic: If root is dict and no explicit keys, use root keys as keywords for custom responses
        if not (data.get("custom_responses") or data.get("templates")) and isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str): # Assuming values are strings for custom responses
                    new_custom_responses[k.lower()] = v

        bot.settings.custom_responses = new_custom_responses
        bot.settings.templates = new_templates

        db.commit()
        clear_cache_for_bot(bot.id)
        # Count the number of items added to both
        count = len(new_custom_responses) + len(new_templates)
        return {"status": "ok", "count": count}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(400, f"Upload failed: {e}")

@router.get("/settings/downloadjson")
def download_json_settings(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")
    s = bot.settings
    return {
        "templates": s.templates or {},
        "custom_responses": s.custom_responses or {},
        "language": s.language,
        "model_name": s.model_name,
        "temperature": s.temperature
    }

class TemplateUpdate(BaseModel):
    content: str
    enabled: bool

@router.put("/templates/{template_id}")
def update_template(template_id: str, data: TemplateUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")
    s = bot.settings
    templates = s.templates or s.custom_responses or {}
    templates[f"template_{template_id}"] = data.content
    templates[f"template_{template_id}_enabled"] = data.enabled
    s.templates = templates
    s.custom_responses = templates
    db.commit()
    clear_cache_for_bot(bot.id)
    return {"status": "ok"}

@router.post("/test-chat")
def test_chat(data: TestChatRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot: raise HTTPException(404, "Bot not found")
    integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
    if not integ: raise HTTPException(404, "Integrations not found")

    products, categories, contact_info_data = [], [], {}
    website_url = integ.woocommerce_url or integ.wp_base_url
    if website_url:
        try:
            prod_res = UniversalWebsiteFetcher.scrape_products_from_website(website_url)
            if prod_res.get("success"):
                products = prod_res.get("products", [])
                categories = prod_res.get("categories", [])
            site_info = UniversalWebsiteFetcher.fetch_site_info(website_url)
            contact_info_data = {
                "site_name": site_info.get("site_name") or website_url,
                "phone": site_info.get("contact", {}).get("phone", ""),
                "email": site_info.get("contact", {}).get("email", ""),
                "address": site_info.get("contact", {}).get("address", ""),
                "services": site_info.get("services", []),
                "about": site_info.get("about", ""),
            }
        except Exception as e:
            logger.warning(f"Failed to fetch website data for test chat: {e}")
            contact_info_data = {"site_name": "Test Store"}

    # Ensure all bot settings are included
    bot_settings = {
        "prompt": bot.settings.prompt if bot.settings else "",
        "model_name": bot.settings.model_name if bot.settings else "openrouter",
        "specific_model_name": bot.settings.specific_model_name if bot.settings else None,
        "api_key": decrypt_value(bot.settings.api_key) if bot.settings and bot.settings.api_key else "",
        "temperature": bot.settings.temperature if bot.settings else 70,
        "language": bot.settings.language if bot.settings else "english",
        "templates": bot.settings.templates if bot.settings else {},
        "custom_responses": bot.settings.custom_responses if bot.settings else {},
        "template_enabled": getattr(bot.settings, 'template_enabled', True) if bot.settings else True,
        "template_statuses": bot.settings.template_statuses if bot.settings else {},
        "_bot_id": bot.id  # Pass bot ID for lead capture
    }

    reply = handle_message(
        bot_mode=bot.mode,
        bot_id=bot.id,
        text=data.message,
        phone="sandbox_test_user",
        name="Test User",
        bot_settings=bot_settings,
        integrations={},
        contact_info=contact_info_data,
        products=products,
        categories=categories,
        business_type=integ.business_type or "product",
        user_plan=get_user_plan(user_id, db),
        user_id=user_id
    )
    return {"reply": reply}
