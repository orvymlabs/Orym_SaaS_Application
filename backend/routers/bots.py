from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Bot, BotSettings, Integration, Message, Lead, User, UserTemplate
from schemas.bot import (
    BotResponse, BotSettingsUpdate, BotModeUpdate, BotStatusUpdate, SettingsResponse,
    TestChatRequest, TestChatResponse
)
from typing import Dict, List, Optional
from services import decode_token
from services.encryption import encrypt_value, decrypt_value
from services.bot_engine import handle_message
from services.ai_service import AVAILABLE_MODELS
from services.plan_enforcement import PlanEnforcementService
from config import get_settings as get_app_settings
from pydantic import BaseModel
import logging
import json

from services.universal_website_fetcher import UniversalWebsiteFetcher
from services.default_bot import clear_cache_for_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["bots"])

def get_plan_limits(plan: str) -> dict:
    """Get plan limits for users."""
    normalized_plan = plan.lower()

    if normalized_plan == "free":
        return {"custom_responses": 3, "custom_products": 10, "custom_templates": 3}
    elif normalized_plan == "starter":
        return {"custom_responses": 10, "custom_products": 100, "custom_templates": 10}
    elif normalized_plan == "premium":
        return {"custom_responses": 0, "custom_products": 0, "custom_templates": 0}
    return {"custom_responses": 3, "custom_products": 10, "custom_templates": 3}

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
        "welcome_message": s.welcome_message,
        "response_delay": s.response_delay or 0,
    }

@router.patch("/settings")
def update_settings(data: BotSettingsUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")

    # Initialize plan enforcement service
    plan_service = PlanEnforcementService(db)

    s = bot.settings
    if data.prompt is not None: s.prompt = data.prompt
    if data.model_name is not None: s.model_name = data.model_name
    if data.specific_model_name is not None: s.specific_model_name = data.specific_model_name
    if data.api_key is not None:
        logger.info(f"Received API key update - Length: {len(data.api_key)}, First 10 chars: {data.api_key[:10]}...")
        s.api_key = encrypt_value(data.api_key)
        logger.info(f"API key encrypted and saved - Encrypted length: {len(s.api_key) if s.api_key else 0}")
    if data.temperature is not None: s.temperature = data.temperature
    if data.language is not None: s.language = data.language

    # Enforce template limits
    if data.templates is not None:
        if data.templates and isinstance(data.templates, dict):
            # Count customized templates (non-empty values)
            new_template_count = sum(1 for k, v in data.templates.items()
                                    if k.startswith('template_') and not k.endswith('_enabled')
                                    and v is not None and v != "")

            # Get plan and check limits
            user_plan = plan_service.get_user_plan(user_id)
            if user_plan and user_plan.max_templates > 0:  # 0 means unlimited
                if new_template_count > user_plan.max_templates:
                    raise HTTPException(
                        403,
                        f"Template limit exceeded. Your {user_plan.display_name} plan allows {user_plan.max_templates} templates. You're trying to save {new_template_count}. Upgrade to add more."
                    )

            templates_size = len(json.dumps(data.templates, ensure_ascii=False).encode('utf-8'))
            logger.debug(f"Received templates payload size: {templates_size} bytes, count: {new_template_count}")

        s.templates = data.templates

    # Enforce rule message limits
    if data.custom_responses is not None:
        if data.custom_responses and isinstance(data.custom_responses, dict):
            new_rule_count = len(data.custom_responses)

            # Get plan and check limits
            user_plan = plan_service.get_user_plan(user_id)
            if user_plan and user_plan.max_rule_based_messages > 0:  # 0 means unlimited
                if new_rule_count > user_plan.max_rule_based_messages:
                    raise HTTPException(
                        403,
                        f"Rule message limit exceeded. Your {user_plan.display_name} plan allows {user_plan.max_rule_based_messages} rule messages. You're trying to save {new_rule_count}. Upgrade to add more."
                    )

            custom_responses_size = len(json.dumps(data.custom_responses, ensure_ascii=False).encode('utf-8'))
            logger.debug(f"Received custom_responses payload size: {custom_responses_size} bytes, count: {new_rule_count}")

        s.custom_responses = data.custom_responses
        logger.info(f"Updated custom_responses: {data.custom_responses}")
    if data.template_enabled is not None: s.template_enabled = data.template_enabled

    # Save template_statuses (Issue 7 - CLAUDE.md)
    if data.template_statuses is not None:
        s.template_statuses = data.template_statuses
        logger.info(f"Updated template_statuses: {data.template_statuses}")

    # Update WhatsApp engine settings
    if data.welcome_message is not None:
        s.welcome_message = data.welcome_message
        logger.info(f"Updated welcome_message")
    if data.response_delay is not None:
        s.response_delay = data.response_delay
        logger.info(f"Updated response_delay: {data.response_delay}")

    # Update custom messages
    if data.fallback_message is not None:
        s.fallback_message = data.fallback_message
        logger.info(f"Updated fallback_message")
    if data.order_error_message is not None:
        s.order_error_message = data.order_error_message
        logger.info(f"Updated order_error_message")
    if data.error_message is not None:
        s.error_message = data.error_message
        logger.info(f"Updated error_message")

    # Measure commit time
    import time
    commit_start_time = time.time()
    db.commit()
    db.expire_all()  # Expire all objects to force fresh reads
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

    # Initialize plan enforcement service
    plan_service = PlanEnforcementService(db)
    user_plan = plan_service.get_user_plan(user_id)

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

        # Enforce rule message limits
        if user_plan and user_plan.max_rule_based_messages > 0:
            rule_count = len(new_custom_responses)
            if rule_count > user_plan.max_rule_based_messages:
                raise HTTPException(
                    403,
                    f"Rule message limit exceeded. Your {user_plan.display_name} plan allows {user_plan.max_rule_based_messages} rule messages. Upload contains {rule_count}. Upgrade to add more."
                )

        # Enforce template limits
        if user_plan and user_plan.max_templates > 0:
            template_count = sum(1 for k, v in new_templates.items()
                               if k.startswith('template_') and not k.endswith('_enabled')
                               and v is not None and v != "")
            if template_count > user_plan.max_templates:
                raise HTTPException(
                    403,
                    f"Template limit exceeded. Your {user_plan.display_name} plan allows {user_plan.max_templates} templates. Upload contains {template_count}. Upgrade to add more."
                )

        bot.settings.custom_responses = new_custom_responses
        bot.settings.templates = new_templates

        db.commit()
        clear_cache_for_bot(bot.id)
        # Count the number of items added to both
        count = len(new_custom_responses) + len(new_templates)
        return {"status": "ok", "count": count}
    except HTTPException:
        raise
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
    """Test chat endpoint with timeout handling and proper error responses."""
    import threading

    logger.info(f"Test chat request from user {user_id}: {data.message}")

    try:
        bot = db.query(Bot).filter(Bot.user_id == user_id).first()
        if not bot:
            logger.error(f"Bot not found for user {user_id}")
            raise HTTPException(404, "Bot not found")

        integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
        if not integ:
            logger.error(f"Integrations not found for bot {bot.id}")
            raise HTTPException(404, "Integrations not found")

        logger.info(f"Bot mode: {bot.mode}, Bot status: {bot.status}")

        # Fetch cached website data for sandbox testing (so AI uses real data)
        from models import SiteInfoCache
        products, categories, contact_info_data = [], [], {"site_name": "Test Store"}

        cache = db.query(SiteInfoCache).filter(SiteInfoCache.bot_id == bot.id).first()
        if cache:
            # Use cached website data
            contact_info_data = {
                "site_name": cache.site_name or "Test Store",
                "site_description": cache.site_description or "",
                "about": cache.about or "",
                "services": cache.services or [],
                "phone": cache.phone or "",
                "email": cache.email or "",
                "address": cache.address or "",
                "hours": cache.hours or ""
            }
            products = cache.products or []
            logger.info(f"Sandbox using cached data: {cache.site_name}, {len(cache.services or [])} services, {len(products)} products")
        else:
            logger.warning(f"No cached data found for bot {bot.id} - sandbox will use minimal test data")

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
            "order_form_template": bot.settings.order_form_template if bot.settings else None,
            "order_confirmation_message": bot.settings.order_confirmation_message if bot.settings else None,
            "order_form_enabled": getattr(bot.settings, 'order_form_enabled', True) if bot.settings else True,
            "form_menu_label": getattr(bot.settings, 'form_menu_label', None) if bot.settings else None,
            "fallback_message": getattr(bot.settings, 'fallback_message', None) if bot.settings else None,
            "order_error_message": getattr(bot.settings, 'order_error_message', None) if bot.settings else None,
            "error_message": getattr(bot.settings, 'error_message', None) if bot.settings else None,
            "_bot_id": bot.id
        }

        logger.info(f"Calling handle_message with mode: {bot.mode}")

        # Call handle_message with timeout using threading
        reply_result = {"reply": None, "error": None}

        def generate_reply():
            try:
                reply_result["reply"] = handle_message(
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
                logger.info(f"Reply generated successfully: {reply_result['reply'][:100] if reply_result['reply'] else 'None'}")
            except Exception as e:
                reply_result["error"] = str(e)
                logger.error(f"Error generating reply: {e}", exc_info=True)

        reply_thread = threading.Thread(target=generate_reply, daemon=True)
        reply_thread.start()
        reply_thread.join(timeout=15)  # 15 second timeout

        if reply_thread.is_alive():
            logger.error("Bot response generation timed out after 15 seconds")
            return {"reply": "⏱️ Response timeout. Your bot is taking too long to respond. If using AI mode, check your API key and model settings.", "mode": bot.mode, "bot_id": bot.id}

        if reply_result["error"]:
            logger.error(f"Reply error: {reply_result['error']}")
            return {"reply": f"❌ Error: {reply_result['error']}", "mode": bot.mode, "bot_id": bot.id}

        if reply_result["reply"] is None:
            logger.error("No reply generated")
            return {"reply": "❌ No response generated. Please check your bot settings.", "mode": bot.mode, "bot_id": bot.id}

        logger.info("Test chat completed successfully")
        return {"reply": reply_result["reply"], "mode": bot.mode, "bot_id": bot.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test chat: {e}", exc_info=True)
        return {"reply": f"❌ Error: {str(e)}", "mode": "error", "bot_id": None}


# Custom Templates CRUD Endpoints
class CustomTemplateCreate(BaseModel):
    template_name: str
    content: str

class CustomTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    content: Optional[str] = None
    position: Optional[int] = None

@router.get("/custom-templates")
def get_custom_templates(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Fetch all custom templates for the logged-in user"""
    templates = db.query(UserTemplate).filter(UserTemplate.user_id == user_id).order_by(UserTemplate.position).all()
    return {"templates": [
        {
            "id": t.id,
            "template_name": t.template_name,
            "content": t.content,
            "position": t.position,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in templates
    ]}

@router.post("/custom-templates")
def create_custom_template(data: CustomTemplateCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Create a new custom template"""
    # Validate template name and content
    if not data.template_name or not data.template_name.strip():
        raise HTTPException(400, "Template name is required")
    if len(data.template_name) > 50:
        raise HTTPException(400, "Template name must be 50 characters or less")
    if not data.content or not data.content.strip():
        raise HTTPException(400, "Template content is required")
    if len(data.content) > 1000:
        raise HTTPException(400, "Template content must be 1000 characters or less")

    # Check plan limits using PlanEnforcementService
    plan_service = PlanEnforcementService(db)
    can_add, message = plan_service.can_add_template(user_id)
    if not can_add:
        raise HTTPException(403, message)

    # Get the highest position and increment
    max_position = db.query(UserTemplate).filter(UserTemplate.user_id == user_id).count()

    new_template = UserTemplate(
        user_id=user_id,
        template_name=data.template_name.strip(),
        content=data.content.strip(),
        position=max_position
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    # Clear cache so menu updates immediately
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if bot:
        clear_cache_for_bot(bot.id)

    return {
        "id": new_template.id,
        "template_name": new_template.template_name,
        "content": new_template.content,
        "position": new_template.position,
        "created_at": new_template.created_at.isoformat() if new_template.created_at else None,
        "updated_at": new_template.updated_at.isoformat() if new_template.updated_at else None,
    }

@router.put("/custom-templates/{template_id}")
def update_custom_template(template_id: int, data: CustomTemplateUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Update an existing custom template"""
    template = db.query(UserTemplate).filter(
        UserTemplate.id == template_id,
        UserTemplate.user_id == user_id
    ).first()

    if not template:
        raise HTTPException(404, "Template not found")

    # Validate and update fields
    if data.template_name is not None:
        if not data.template_name.strip():
            raise HTTPException(400, "Template name cannot be empty")
        if len(data.template_name) > 50:
            raise HTTPException(400, "Template name must be 50 characters or less")
        template.template_name = data.template_name.strip()

    if data.content is not None:
        if not data.content.strip():
            raise HTTPException(400, "Template content cannot be empty")
        if len(data.content) > 1000:
            raise HTTPException(400, "Template content must be 1000 characters or less")
        template.content = data.content.strip()

    if data.position is not None:
        template.position = data.position

    db.commit()
    db.refresh(template)

    # Clear cache so menu updates immediately
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if bot:
        clear_cache_for_bot(bot.id)

    return {
        "id": template.id,
        "template_name": template.template_name,
        "content": template.content,
        "position": template.position,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }

@router.delete("/custom-templates/{template_id}")
def delete_custom_template(template_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Delete a custom template"""
    template = db.query(UserTemplate).filter(
        UserTemplate.id == template_id,
        UserTemplate.user_id == user_id
    ).first()

    if not template:
        raise HTTPException(404, "Template not found")

    db.delete(template)
    db.commit()

    # Clear cache so menu updates immediately
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if bot:
        clear_cache_for_bot(bot.id)

    return {"status": "ok", "message": "Template deleted successfully"}


# Order Form Settings Endpoints
class OrderFormSettings(BaseModel):
    order_form_template: Optional[str] = None
    order_confirmation_message: Optional[str] = None
    order_form_enabled: Optional[bool] = None
    form_menu_label: Optional[str] = None
    fallback_message: Optional[str] = None
    order_error_message: Optional[str] = None
    error_message: Optional[str] = None

@router.get("/order-form/settings")
def get_order_form_settings(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Fetch order form template, confirmation message, and enabled status for logged in user"""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot settings not found")

    s = bot.settings

    # Default values if not set
    default_form_template = """🛍️ Order Form

Please fill in the details below and reply:

Full Name:
Phone Number:
Delivery Address:
Product / Item:
Quantity:
Special Instructions (optional):"""

    default_confirmation = """✅ Thank you! Your order has been received.
Our team will contact you shortly to confirm."""

    return {
        "order_form_template": s.order_form_template or default_form_template,
        "order_confirmation_message": s.order_confirmation_message or default_confirmation,
        "order_form_enabled": s.order_form_enabled if s.order_form_enabled is not None else True,
        "form_menu_label": s.form_menu_label or "",
        "fallback_message": getattr(s, 'fallback_message', None) or "",
        "order_error_message": getattr(s, 'order_error_message', None) or "",
        "error_message": getattr(s, 'error_message', None) or ""
    }

@router.put("/order-form/settings")
def update_order_form_settings(data: OrderFormSettings, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Save order form template, confirmation message, and enabled status"""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot settings not found")

    s = bot.settings

    # Validate and update fields
    # First, update order_form_enabled if provided
    if data.order_form_enabled is not None:
        s.order_form_enabled = data.order_form_enabled

    # Only validate order form template if order form is enabled
    if data.order_form_template is not None:
        # If order form is disabled, allow empty template
        if s.order_form_enabled and not data.order_form_template.strip():
            raise HTTPException(400, "Order form template cannot be empty when order form is enabled")
        if data.order_form_template.strip() and len(data.order_form_template) > 1000:
            raise HTTPException(400, "Order form template must be 1000 characters or less")
        s.order_form_template = data.order_form_template.strip() if data.order_form_template.strip() else None

    # Only validate confirmation message if order form is enabled
    if data.order_confirmation_message is not None:
        # If order form is disabled, allow empty confirmation message
        if s.order_form_enabled and not data.order_confirmation_message.strip():
            raise HTTPException(400, "Order confirmation message cannot be empty when order form is enabled")
        if data.order_confirmation_message.strip() and len(data.order_confirmation_message) > 500:
            raise HTTPException(400, "Order confirmation message must be 500 characters or less")
        s.order_confirmation_message = data.order_confirmation_message.strip() if data.order_confirmation_message.strip() else None

    # Update form menu label
    if data.form_menu_label is not None:
        if data.form_menu_label.strip() and len(data.form_menu_label) > 30:
            raise HTTPException(400, "Form menu label must be 30 characters or less")
        s.form_menu_label = data.form_menu_label.strip() if data.form_menu_label.strip() else None

    # Update custom messages
    if data.fallback_message is not None:
        s.fallback_message = data.fallback_message.strip() if data.fallback_message.strip() else None

    if data.order_error_message is not None:
        s.order_error_message = data.order_error_message.strip() if data.order_error_message.strip() else None

    if data.error_message is not None:
        s.error_message = data.error_message.strip() if data.error_message.strip() else None

    db.commit()
    db.expire_all()  # Expire all objects in session to force fresh reads
    clear_cache_for_bot(bot.id)

    return {"status": "ok", "message": "Order form settings saved successfully"}

