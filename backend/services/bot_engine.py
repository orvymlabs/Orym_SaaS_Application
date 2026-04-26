"""
Bot Engine — Intelligent Routing with Plan-based Feature Gating (No Product Features)
"""
import re
import logging
from typing import Optional
from .default_bot import process as default_process, _get_contact_info, _get_services
from .ai_service import ai_reply

logger = logging.getLogger(__name__)

PLAN_ERROR = "⚠️ This feature is available in Growth plan. Please upgrade."


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
            return _get_services(bot_settings)

        elif tl.startswith("2") or "delivery" in tl or "shipping" in tl:
             # In new simplified menu, 2 is Delivery Info
             from .default_bot import _get_delivery_info
             return _get_delivery_info(bot_settings)

        elif tl.startswith("3") or "contact" in tl:
            # In new simplified menu, 3 is Contact Us
            return _get_contact_info(bot_settings, contact_info)

        if _is_website_query(text):
            if "service" in tl or business_type == "service":
                return _get_services(bot_settings)
            return _get_contact_info(bot_settings, contact_info)

        # Keyword Engine logic
        custom = bot_settings.get("custom_responses") or bot_settings.get("templates") or {}
        for keyword, response in custom.items():
            if keyword.lower() in tl:
                return response.replace("{name}", name or "Customer").replace("{phone}", phone).replace("{last_message}", text)

        # AI Fallback if API key exists
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
