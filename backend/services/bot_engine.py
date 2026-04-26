"""
Bot Engine — Intelligent Routing with Plan-based Feature Gating
"""
import re
import logging
from typing import Optional
from .default_bot import process as default_process, _t_all_products, _get_contact_info, _get_services, PRODUCT_LIMIT_WARNING
from .ai_service import ai_reply

logger = logging.getLogger(__name__)

PLAN_ERROR = "⚠️ This feature is available in Growth plan. Please upgrade."


def _is_product_query(text: str, categories: list) -> bool:
    tl = text.lower()
    product_keywords = ['product', 'products', 'price', 'buy', 'order', 'cost', 'rate', 'catalog', 'item', 'items', 'stock', 'samaan', 'list']
    if any(w in tl for w in product_keywords):
        return True
    for cat in categories:
        if cat.lower() in tl:
            return True
    return False


def _is_website_query(text: str) -> bool:
    tl = text.lower()
    return any(w in tl for w in ['about', 'contact', 'service', 'services', 'address', 'phone', 'email', 'location', 'website', 'info'])


def handle_message(bot_mode: str, bot_id: int, text: str, phone: str, name: str,
                   bot_settings: dict, integrations: dict, contact_info: dict,
                   products: list, categories: list, business_type: str = "product",
                   user_plan: str = "starter") -> str:

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
            contact_info=contact_info
        )

    # PREDEFINED MODE
    if bot_mode == "predefined":

        if tl.startswith("1") or "service" in tl or "serivce" in tl:
            return _get_services(contact_info.get("services"), lang)

        elif tl.startswith("2") or "product" in tl or "products" in tl or "catalog" in tl:
            if user_plan == "free":
                return "⚠️ Product features are not available in Free plan. Please upgrade to Starter or Growth plan."

            if products:
                display_count = 10 if user_plan == "starter" else len(products)
                items = [f"• {p.get('name','')} - {p.get('price','Contact')} PKR" for p in products[:display_count]]
                result = _t_all_products(items, len(products))

                if user_plan == "starter" and len(products) > 10:
                    result += "\n\n" + PRODUCT_LIMIT_WARNING

                return result
            else:
                return "I can't find any products right now. Please check back later or contact us for more information."

        elif tl.startswith("3") or "order" in tl or "buy" in tl:
            if products:
                display_count = 10 if user_plan == "starter" else len(products)
                items = [f"• {p.get('name','')} - {p.get('price','Contact')} PKR" for p in products[:display_count]]
                result = _t_all_products(items, len(products))

                if user_plan == "starter" and len(products) > 10:
                    result += "\n\n" + PRODUCT_LIMIT_WARNING

                return result
            else:
                return _get_contact_info(contact_info, lang=lang) or "You can find order information on our website or by contacting us."

        elif tl.startswith("4") or "contact" in tl:
            return _get_contact_info(contact_info, lang=lang)

        if _is_website_query(text):
            if "service" in tl or business_type == "service":
                return _get_services(contact_info.get("services"), lang)
            return _get_contact_info(contact_info, lang=lang)

        custom = bot_settings.get("custom_responses") or bot_settings.get("templates") or {}
        for keyword, response in custom.items():
            if keyword.lower() in tl:
                return response.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

        if api_key:
            ai_resp = ai_reply(text, lang, api_key, provider, prompt, temp, contact_info, products, categories, model_name=specific_model, business_type=business_type)
            if ai_resp:
                return ai_resp

        return "I'm sorry, I couldn't find that information. Please type *menu* to see available options."

    # AI MODE
    if bot_mode == "ai":
        if not api_key:
            return "⚠️ AI assistant is not configured. Please add your API key in settings."

        ai_resp = ai_reply(
            text, lang, api_key, provider, prompt, temp,
            contact_info, products, categories,
            model_name=specific_model,
            business_type=business_type,
            user_plan=user_plan
        )

        if ai_resp:
            return ai_resp

        return "I'm having trouble connecting to my brain. Please try again in a moment!"

    return default_process(
        bot_id, text, phone, name,
        business_type=business_type,
        user_plan=user_plan,
        products=products,
        contact_info=contact_info
    )