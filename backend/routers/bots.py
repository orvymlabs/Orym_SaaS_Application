from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Bot, BotSettings, Integration, Message, Lead, User # Assuming BotSettings has template_enabled, website_url and a field for templates
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
import json # Import json for handling cached categories if needed

# Import UniversalWebsiteFetcher for proactive fetching in AI mode
from services.universal_website_fetcher import UniversalWebsiteFetcher


def get_plan_limits(plan: str) -> dict:
    """Get limits based on user plan."""
    if plan == "growth":
        return {"custom_responses": -1, "custom_products": -1}  # unlimited
    return {"custom_responses": 10, "custom_products": 20}  # Increased from 5/10


def get_user_plan(user_id: int, db: Session) -> str:
    """Get user plan from database."""
    user = db.query(User).filter(User.id == user_id).first()
    return user.plan if user else "starter"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["bots"])


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
    """Get available AI models per provider."""
    return AVAILABLE_MODELS


# Default system templates
DEFAULT_TEMPLATES = {
    "greeting": {
        "id": "greeting",
        "name": "Welcome Greeting",
        "logic": "The first message a user sees when they type 'Hi' or 'Hello'.",
        "placeholder": "👋 Hi {user_name}! Welcome to {site_name}. I'm your virtual assistant, here to help you with orders, inquiries, or just answering your questions. How can I assist you today?",
        "enabled": True
    },
    "menu": {
        "id": "menu",
        "name": "Main Menu",
        "logic": "The navigation hub. Triggered by typing 'Menu' or after the greeting.",
        "placeholder": """📋 *Main Menu*
Select an option to get started:
1️⃣ 🛍️ Order Products
2️⃣ 💰 Ask About Pricing
3️⃣ 🚚 Delivery Info
4️⃣ 📞 Contact Us
5️⃣ ℹ️ Services
💬 Just reply with a number or keyword!""",
        "enabled": True
    },
    "delivery": {
        "id": "delivery",
        "name": "Delivery Information",
        "logic": "Triggered when user selects Delivery. Explains shipping times.",
        "placeholder": """🚚 *Shipping Information*

We offer fast nationwide delivery within 3-5 business days. Let us know if you need any help with your tracking!""",
        "enabled": True
    },
    "contact": {
        "id": "contact",
        "name": "Contact Details",
        "logic": "Triggered when user selects Contact. Shows business info.",
        "placeholder": """📞 *Reach Out to Us*
Need assistance? We are here to help!
🏢 {site_name}
📱 {phone}
📧 {email}
📍 {address}
Feel free to ask any questions!""",
        "enabled": True
    },
    "product_list": {
        "id": "product_list",
        "name": "Product Catalog",
        "logic": "Triggered when user selects Catalog or types 'products'.",
        "placeholder": """🛍️ *Product Catalog* ({total} items)

{item_list}

💬 Reply with a product name to order!""",
        "enabled": True
    },
    "service": {
        "id": "service",
        "name": "Service Information",
        "logic": "Triggered when user selects Services or asks about services offered.",
        "placeholder": """ℹ️ *Our Services*

We offer a range of professional services including:
- Web Development
- AI Integration
- Cloud Solutions

Visit our website or contact us for more details!""",
        "enabled": True
    },
    "order_confirmation": {
        "id": "order_confirmation",
        "name": "Order Confirmation",
        "logic": "Sent after a successful order is placed. Confirms order details.",
        "placeholder": """✅ *Order Confirmed!*

Thank you for your order, {user_name}!
Order ID: {order_id}
Items: {item_list}
Total: {total_amount}

We'll notify you once your order has been shipped. Estimated delivery: {estimated_delivery_date}""",
        "enabled": True
    },
    "farewell": {
        "id": "farewell",
        "name": "Goodbye Message",
        "logic": "Sent when user ends conversation or says goodbye.",
        "placeholder": """👋 Thank you for chatting with us!

If you have any more questions, feel free to reach out anytime. Have a great day!""",
        "enabled": False
    },
    "out_of_hours": {
        "id": "out_of_hours",
        "name": "Out of Hours",
        "logic": "Sent when user messages outside business hours.",
        "placeholder": """🌙 Thanks for reaching out!

Our business hours are 9 AM - 6 PM (Mon-Sat). We'll get back to you first thing tomorrow morning!""",
        "enabled": False
    },
    "fallback": {
        "id": "fallback",
        "name": "Fallback Response",
        "logic": "Default response when no other template matches.",
        "placeholder": """🤔 I'm not sure I understand.

You can ask me about:
• Products and pricing
• Delivery information
• Contact details
• Our services

Or type *menu* to see all options!""",
        "enabled": True
    }
}


@router.get("/templates")
def get_automation_templates():
    """Get predefined automation templates for the system flow."""
    return {"system_flow": list(DEFAULT_TEMPLATES.values())}


@router.get("/user-templates")
def get_user_templates(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get user's customized templates with enabled/disabled status."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    s = bot.settings
    user_templates = s.templates or s.custom_responses or {}

    # Build response with default templates merged with user customizations
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

    # Add user's custom templates (non-system)
    system_ids = list(DEFAULT_TEMPLATES.keys())
    for key, value in user_templates.items():
        if not any(key.startswith(f"template_{sid}") for sid in system_ids):
            result.append({
                "id": key,
                "name": key.replace("_", " ").title(),
                "logic": "Custom user-defined template",
                "placeholder": value,
                "content": value,
                "enabled": True,
                "is_customized": True,
                "type": "custom"
            })

    return {"templates": result}


@router.patch("/mode")
def update_mode(data: BotModeUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    if data.mode not in ("default", "predefined", "ai"):
        raise HTTPException(400, "Invalid mode. Must be: default, predefined, ai")

    # Validate API key when switching to AI mode
    if data.mode == "ai" and bot.settings:
        if not bot.settings.api_key:
            raise HTTPException(400, "API key is required to enable AI mode. Please add your API key in settings first.")

    bot.mode = data.mode
    db.commit()
    db.refresh(bot)
    return bot


@router.patch("/status")
def update_status(data: BotStatusUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")
    bot.status = data.status
    db.commit()
    return {"status": "ok", "bot_status": bot.status}


@router.get("/settings", response_model=SettingsResponse)
def get_settings(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")
    s = bot.settings
    
    # Priority for templates in settings UI: templates column, then custom_responses
    display_templates = s.templates if s.templates else s.custom_responses
    
    return {
        "id": s.id,
        "bot_id": s.bot_id,
        "prompt": s.prompt,
        "model_name": s.model_name,
        "specific_model_name": s.specific_model_name,
        "temperature": s.temperature,
        "language": s.language,
        "templates": display_templates or {},
        "template_enabled": getattr(s, 'template_enabled', False),
        "custom_products": s.custom_products,
        "has_api_key": bool(s.api_key),
    }


@router.patch("/settings")
def update_settings(data: BotSettingsUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Settings not found")

    s = bot.settings
    user_plan = get_user_plan(user_id, db)
    limits = get_plan_limits(user_plan)

    # Update basic settings
    if data.prompt is not None: s.prompt = data.prompt
    if data.model_name is not None: s.model_name = data.model_name
    if data.specific_model_name is not None: s.specific_model_name = data.specific_model_name
    if data.api_key is not None:
        if not data.api_key.strip():
            raise HTTPException(400, "API key cannot be empty")
        s.api_key = encrypt_value(data.api_key)
    if data.temperature is not None: s.temperature = data.temperature
    if data.language is not None: s.language = data.language

    # Sync templates to BOTH columns for maximum compatibility
    if data.templates is not None:
        system_ids = ['greeting', 'menu', 'delivery', 'contact', 'product_list', 'service', 'order_confirmation']
        custom_rules_count = sum(1 for k in data.templates.keys() if not any(sys_id in k for sys_id in system_ids))
        
        if limits["custom_responses"] != -1 and custom_rules_count > limits["custom_responses"]:
            raise HTTPException(400, f"Your {user_plan} plan allows only {limits['custom_responses']} custom rules.")
        
        s.templates = data.templates
        s.custom_responses = data.templates
        
    if data.template_enabled is not None:
        s.template_enabled = data.template_enabled

    if data.custom_products is not None:
        if limits["custom_products"] != -1 and len(data.custom_products) > limits["custom_products"]:
            raise HTTPException(400, f"Your {user_plan} plan allows only {limits['custom_products']} custom products.")
        s.custom_products = data.custom_products

    db.commit()
    db.refresh(s)
    return {"status": "ok"}


@router.post("/settings/import")
async def import_settings(request: Request, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Import predefined rules from JSON."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")
        
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(400, "Invalid JSON format. Expected a dictionary.")

        user_plan = get_user_plan(user_id, db)
        limits = get_plan_limits(user_plan)
        
        # Extract items to import, handling different possible JSON structures
        # Expecting JSON like: {"custom_responses": {...}, "templates": {...}} or just {"keyword": "response"}
        imported_items = {}
        if isinstance(data.get("custom_responses"), dict):
            imported_items.update(data["custom_responses"])
        if isinstance(data.get("templates"), dict):
            imported_items.update(data["templates"])
        
        # If no explicit keys found, assume the root JSON object contains the rules
        if not imported_items and data:
            imported_items = data

        # Apply limits based on the combined import size
        if limits["custom_responses"] != -1 and len(imported_items) > limits["custom_responses"]:
            items = list(imported_items.items())[:limits["custom_responses"]]
            imported_items = dict(items)
            logger.info(f"Import truncated to {limits['custom_responses']} for {user_plan} plan.")

        # Update bot settings - ensure merging works correctly
        current_custom_responses = bot.settings.custom_responses or {}
        current_custom_responses.update(imported_items)
        bot.settings.custom_responses = current_custom_responses

        current_templates = bot.settings.templates or {}
        current_templates.update(imported_items)
        bot.settings.templates = current_templates
        
        db.commit()
        return {"status": "ok", "count": len(imported_items)}
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        raise HTTPException(400, f"Import failed: {str(e)}")


class TemplateUpdate(BaseModel):
    content: str
    enabled: bool


class TemplateCreate(BaseModel):
    name: str
    content: str
    logic: Optional[str] = "Custom template"


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    data: TemplateUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a specific template's content and enabled status."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    s = bot.settings
    templates = s.templates or s.custom_responses or {}

    # Update template content and enabled status
    templates[f"template_{template_id}"] = data.content
    templates[f"template_{template_id}_enabled"] = data.enabled

    s.templates = templates
    s.custom_responses = templates
    db.commit()

    return {"status": "ok", "template_id": template_id, "enabled": data.enabled}


@router.post("/templates")
def create_template(
    data: TemplateCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new custom template."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    s = bot.settings
    templates = s.templates or s.custom_responses or {}

    # Generate unique ID for custom template
    template_id = f"custom_{data.name.lower().replace(' ', '_')}"

    user_plan = get_user_plan(user_id, db)
    limits = get_plan_limits(user_plan)

    # Count custom templates (excluding system templates)
    system_ids = list(DEFAULT_TEMPLATES.keys())
    custom_count = sum(1 for k in templates.keys() if not any(k.startswith(f"template_{sid}") for sid in system_ids))

    if limits["custom_responses"] != -1 and custom_count >= limits["custom_responses"]:
        raise HTTPException(400, f"Your {user_plan} plan allows only {limits['custom_responses']} custom templates.")

    templates[template_id] = data.content
    templates[f"{template_id}_name"] = data.name
    templates[f"{template_id}_logic"] = data.logic or "Custom template"

    s.templates = templates
    s.custom_responses = templates
    db.commit()

    return {"status": "ok", "template_id": template_id}


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a custom template."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    # Prevent deletion of system templates
    if template_id in DEFAULT_TEMPLATES:
        raise HTTPException(400, "Cannot delete system templates. You can only disable them.")

    s = bot.settings
    templates = s.templates or s.custom_responses or {}

    # Remove template and related keys
    keys_to_remove = [k for k in templates.keys() if k == template_id or k.startswith(f"{template_id}_")]
    for key in keys_to_remove:
        del templates[key]

    s.templates = templates
    s.custom_responses = templates
    db.commit()

    return {"status": "ok", "deleted": template_id}


@router.post("/templates/{template_id}/reset")
def reset_template(
    template_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Reset a template to its default content."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(404, "Template not found")

    s = bot.settings
    templates = s.templates or s.custom_responses or {}

    # Remove custom content to fall back to default
    keys_to_remove = [k for k in templates.keys() if k.startswith(f"template_{template_id}")]
    for key in keys_to_remove:
        del templates[key]

    s.templates = templates
    s.custom_responses = templates
    db.commit()

    return {"status": "ok", "reset": template_id}


@router.post("/templates/bulk-update")
def bulk_update_templates(
    templates_data: Dict[str, TemplateUpdate],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Bulk update multiple templates at once."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot or not bot.settings:
        raise HTTPException(404, "Bot not found")

    s = bot.settings
    templates = s.templates or s.custom_responses or {}

    for template_id, update_data in templates_data.items():
        templates[f"template_{template_id}"] = update_data.content
        templates[f"template_{template_id}_enabled"] = update_data.enabled

    s.templates = templates
    s.custom_responses = templates
    db.commit()

    return {"status": "ok", "updated_count": len(templates_data)}


@router.post("/test-chat")
def test_chat(data: TestChatRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Test chat endpoint - simulates WhatsApp message without webhook."""
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")

    # Get integration
    integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")

    # --- Start: Fetching data for Bot Modes ---
    products_data = []
    categories_data = []
    contact_info_data = {}
    fetched_business_type = integ.business_type or "product" # Default to product
    user_plan = get_user_plan(user_id, db)

    # Fetch bot settings
    settings_db = db.query(BotSettings).filter(BotSettings.bot_id == bot.id).first()
    bot_settings_config = {
        "prompt": settings_db.prompt if settings_db else "",
        "model_name": settings_db.model_name if settings_db else "openrouter",
        "specific_model_name": settings_db.specific_model_name if settings_db else None,
        "api_key": decrypt_value(settings_db.api_key) if settings_db and settings_db.api_key else "",
        "temperature": settings_db.temperature if settings_db else 70,
        "language": settings_db.language if settings_db else "english",
        "templates": settings_db.templates if settings_db else {},
        "custom_responses": settings_db.custom_responses if settings_db else {},
        "template_enabled": getattr(settings_db, 'template_enabled', True) if settings_db else True,
        "custom_products": settings_db.custom_products if settings_db else {},
    }

    # Always attempt to fetch website data if URL is present, for all modes in sandbox
    if integ.woocommerce_url:
        website_url = integ.woocommerce_url
        logger.info(f"Sandbox ({bot.mode}): Attempting to fetch data from website: {website_url}")
        
        # 1. Fetch products
        prod_res = UniversalWebsiteFetcher.scrape_products_from_website(website_url)
        if prod_res["success"]:
            products_data = prod_res.get("products", [])
            categories_data = prod_res.get("categories", [])
            logger.info(f"Sandbox: Fetched {len(products_data)} products")
        
        # 2. Fetch site info
        site_info = UniversalWebsiteFetcher.fetch_site_info(website_url)
        contact_info_data = {
            "site_name": site_info.get("site_name") or website_url,
            "site_description": site_info.get("site_description", ""),
            "about": site_info.get("about", ""),
            "services": site_info.get("services", []),
            "phone": site_info.get("contact", {}).get("phone", ""),
            "email": site_info.get("contact", {}).get("email", ""),
            "address": site_info.get("contact", {}).get("address", ""),
            "hours": site_info.get("contact", {}).get("hours", "")
        }
        logger.info(f"Sandbox: Fetched site info for {website_url}")

    # --- End: Fetching data for Bot Modes ---
    
    # Use cached products if available and no specific website fetch occurred or failed
    # This logic might need refinement: prefer fetched data over cached if fetch was successful
    # For now, assuming fetched_products takes precedence if fetch was successful.
    # If fetch failed, we might want to fall back to cached, but this `test-chat` doesn't easily access integration cache.
    # For `test-chat`, we are performing a LIVE fetch, so cached data is less relevant unless `auto_discover` needs to use it.

    # Decrypt credentials and check for cached products (Original logic for WooCommerce API fallback)
    woo_key = woo_secret = ""
    woo_url = wp_url = ""
    # has_cached_products = False # Assume no cached products if we are doing a fresh fetch - this variable is unused currently

    if integ.woo_consumer_key:
        try:
            woo_key = decrypt_value(integ.woo_consumer_key)
            woo_secret = decrypt_value(integ.woo_consumer_secret)
            woo_url = integ.woocommerce_url or integ.wp_base_url or "https://example.com"
            wp_url = integ.wp_base_url or woo_url
        except Exception:
            pass

    # If website fetch didn't yield products, use WooCommerce API fallback IF configured
    # This block is now less relevant as website_url is not fetched here, but kept for WooCommerce fallback logic
    # if not products_data and fetched_website_url and woo_key and woo_url and fetched_business_type == "product":
    #     logger.info(f"AI Mode: Website fetch yielded no products, attempting WooCommerce API fallback for {woo_url}")
    #     woo_prod_res = UniversalWebsiteFetcher.fetch_products_with_auth(woo_url, woo_key, woo_secret)
    #     if woo_prod_res["success"]:
    #         products_data = woo_prod_res.get("products", [])
    #         categories_data = json.loads(woo_prod_res.get("categories", "[]"))
    #         # Update business type if it was inferred as service but WC products are found
    #         fetched_business_type = "product"
    #         logger.info(f"AI Mode: WooCommerce API fallback successful, fetched {len(products_data)} products.")


    # If still no products, use default credentials
    if not products_data and (not woo_key or woo_key == ""):
        app_settings = get_app_settings()
        # Fallback to default if no integration credentials and no fetched data
        # REMOVED: fetched_website_url is no longer available here. This part needs reconsideration if default contact info is still needed.
        # if fetched_website_url: # If fetch was attempted but yielded nothing, use default contact info for site name etc.
        #     default_contact_info = UniversalWebsiteFetcher.fetch_site_info(fetched_website_url)
        #     contact_info_data = default_contact_info.get("contact", {})
        #     fetched_business_type = default_contact_info.get("business_type", "product") # Use discovered type or default
        # else:
        # If no website URL was even configured, use generic defaults
        contact_info_data = {
            "site_name": app_settings.APP_NAME,
            "phone": "+1234567890",
            "email": "support@example.com",
            "address": "123 Main St, Anytown, USA"
        }

    # If business type is still 'product' but we have no products, maybe it's a service?
    if fetched_business_type == "product" and not products_data and not contact_info_data.get("services"):
        logger.info("AI Mode: Detected product mode but no products found. Re-evaluating business type to service.")
        fetched_business_type = "service"

    # Construct the final contact_info dictionary to pass to handle_message
    # Prioritize fetched data, then cached (if implemented elsewhere), then defaults
    final_contact_info = {
        "site_name": contact_info_data.get("site_name") or bot_settings_config.get("site_name", "our business"),
        "phone": contact_info_data.get("phone") or bot_settings_config.get("phone", ""),
        "email": contact_info_data.get("email") or bot_settings_config.get("email", ""),
        "address": contact_info_data.get("address") or bot_settings_config.get("address", ""),
        "hours": contact_info_data.get("hours") or bot_settings_config.get("hours", ""),
        "services": contact_info_data.get("services") or [],
        "site_description": contact_info_data.get("site_description", ""),
        "about": contact_info_data.get("about", ""),
    }


    # Route through bot engine with plan check
    reply = handle_message(
        bot_mode=bot.mode,
        bot_id=bot.id,
        text=data.message,
        phone="test_phone",
        name="Test User",
        bot_settings=bot_settings_config, # Pass the collected settings
        integrations={
            "woo_key": woo_key, "woo_secret": woo_secret, "woo_url": woo_url,
            "wp_url": wp_url, "whatsapp_token": None,
            "phone_number_id": integ.phone_number_id,
        },
        contact_info=final_contact_info, # Pass the consolidated contact info
        products=products_data, # Pass fetched or fallback products
        categories=categories_data, # Pass fetched categories
        business_type=fetched_business_type, # Pass determined business type
        user_plan=user_plan
    )

    # Save messages to DB
    db_msg_user = Message(
        bot_id=bot.id,
        sender="user",
        phone_number="test_phone",
        message=data.message,
        seen=True,  # Mark as seen
    )
    db.add(db_msg_user)
    db.flush()

    if reply:
        db_msg_bot = Message(
            bot_id=bot.id,
            sender="bot",
            phone_number="test_phone",
            message=reply[:1000],
            seen=True,  # Mark as seen
        )
        db.add(db_msg_bot)

    db.commit()

    return {"reply": reply or "No response generated", "mode": bot.mode, "bot_id": bot.id}

# --- Placeholder helper functions, need actual implementation ---
def default_refresh(bot_id: int, woo_key: str, woo_secret: str, woo_url: str, stores_url: str, wp_url: str):
    """Placeholder for refreshing cache data. Needs implementation."""
    # This function is called in test-chat but not defined in the provided snippet.
    # In a real scenario, this would trigger cache updates for products/categories.
    # For now, it's a no-op, relying on live fetches or direct data passing.
    logger.debug(f"Placeholder: default_refresh called for bot {bot_id}")
    pass

def _get_cache(bot_id: int):
    """Placeholder for getting cache data. Needs implementation."""
    # This function is called in test-chat but not defined.
    # Returns empty dict, meaning no cached data is used in this test context.
    logger.debug(f"Placeholder: _get_cache called for bot {bot_id}")
    return {}
