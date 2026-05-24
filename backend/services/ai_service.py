"""Multi-provider AI service.

Supported providers (set via bot_settings.model_name):
  - openai
  - gemini
  - openrouter
  - qwen
"""
import time
import json
import threading
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_rate_lock = threading.Lock()
_last_429 = 0
_last_req = 0

# Available models per provider (latest paid versions)
AVAILABLE_MODELS: Dict[str, list] = {
    "openai": [
        {"value": "gpt-4o", "label": "GPT-4o (Latest)", "type": "paid"},
        {"value": "gpt-4o-mini", "label": "GPT-4o Mini (Fast)", "type": "paid"},
        {"value": "o1", "label": "O1 (Reasoning)", "type": "paid"},
        {"value": "o1-mini", "label": "O1 Mini", "type": "paid"},
        {"value": "o3-mini", "label": "O3 Mini", "type": "paid"},
    ],
    "openrouter": [
        {"value": "openai/gpt-4o", "label": "GPT-4o", "type": "paid"},
        {"value": "anthropic/claude-3.5-sonnet", "label": "Claude 3.5 Sonnet", "type": "paid"},
        {"value": "google/gemini-pro-1.5", "label": "Gemini Pro 1.5", "type": "paid"},
        {"value": "meta-llama/llama-3.1-70b-instruct", "label": "Llama 3.1 70B", "type": "paid"},
        {"value": "openai/gpt-oss-20b:free", "label": "GPT-OSS 20B (Free)", "type": "free"},
    ],
    "gemini": [
        {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash", "type": "paid"},
        {"value": "gemini-2.0-pro", "label": "Gemini 2.0 Pro", "type": "paid"},
        {"value": "gemini-2.0-flash-lite", "label": "Gemini 2.0 Flash Lite", "type": "paid"},
    ],
    "qwen": [
        {"value": "qwen-plus", "label": "Qwen Plus", "type": "paid"},
        {"value": "qwen-max", "label": "Qwen Max", "type": "paid"},
        {"value": "qwen-turbo", "label": "Qwen Turbo (Fast)", "type": "paid"},
        {"value": "qwen-long", "label": "Qwen Long", "type": "paid"},
    ],
}

# Provider configurations
PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "header": "Authorization",
        "header_fmt": "Bearer {key}",
        "extra_headers": {"HTTP-Referer": "https://example.com", "X-Title": "WhatsApp Bot"},
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "header": "Authorization",
        "header_fmt": "Bearer {key}",
        "extra_headers": {},
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "header": "Authorization",
        "header_fmt": "Bearer {key}",
        "extra_headers": {},
    },
    "qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "header": "Authorization",
        "header_fmt": "Bearer {key}",
        "extra_headers": {},
    },
}


def ai_reply(text: str, lang: str, api_key: str, provider: str,
             prompt: str, temperature: float, contact: dict,
             products: list, categories: list, model_name: str = None,
             business_type: str = "product", user_plan: str = "starter") -> Optional[str]:
    """Call AI API with the specified provider.

    Args:
        provider: "openai", "gemini", "openrouter", or "qwen"
        temperature: 0.0 to 1.0
        model_name: Specific model to use (optional, uses provider default if not set)
        business_type: "product" or "service"
        user_plan: "starter" or "premium" - affects what info AI can share
    """
    if not api_key or not api_key.strip():
        logger.error("AI mode: API key is empty or None")
        return None

    api_key = api_key.strip()
    logger.info(f"AI mode: Using provider '{provider}' with key '{api_key[:10]}...'")

    global _last_429, _last_req
    with _rate_lock:
        if _last_429 > 0 and (time.time() - _last_429) < 5:
            logger.warning("AI request skipped due to recent rate limit")
            return None
        wait = 0.8 - (time.time() - _last_req)
        if wait > 0:
            time.sleep(wait)
        _last_req = time.time()

    lang_map = {
        'english': "ALWAYS respond in English. Do NOT use Hindi, Urdu, or other languages.",
        'roman_urdu': "Respond in Roman Urdu (Urdu written in English script, like 'Aap kaise hain?'). Only use Roman Urdu if the user explicitly requests it.",
        'urdu': "Respond in Urdu script (اردو). Only use Urdu if the user explicitly requests it."
    }

    # Detect if user is requesting a specific language in their message
    user_text_lower = text.lower()
    language_requests = {
        'urdu': any(phrase in user_text_lower for phrase in ['urdu', 'اردو', 'talk in urdu', 'speak urdu']),
        'hindi': any(phrase in user_text_lower for phrase in ['hindi', 'हिंदी', 'talk in hindi', 'speak hindi']),
        'roman_urdu': any(phrase in user_text_lower for phrase in ['roman urdu', 'urdu in english']),
        'english': any(phrase in user_text_lower for phrase in ['english', 'talk in english', 'speak english']),
    }

    # Override language if user explicitly requests it
    if language_requests['urdu']:
        lang_instruction = "\n\n## LANGUAGE:\nRespond in Urdu script (اردو) as the user requested."
    elif language_requests['hindi']:
        lang_instruction = "\n\n## LANGUAGE:\nRespond in Hindi (हिंदी) as the user requested."
    elif language_requests['roman_urdu']:
        lang_instruction = "\n\n## LANGUAGE:\nRespond in Roman Urdu as the user requested."
    elif lang and lang.lower() != 'auto':
        lang_instruction = f"\n\n## LANGUAGE:\n{lang_map.get(lang, 'Respond in English')}"
    else:
        lang_instruction = ""

    # Build website info section
    site_name = contact.get('site_name', 'our business')
    site_desc = contact.get('site_description', '')
    about = contact.get('about', '')
    services = contact.get('services', [])

    # Extract contact details with fallbacks
    contact_phone = contact.get('phone', '')
    contact_email = contact.get('email', '')
    contact_address = contact.get('address', '')
    contact_hours = contact.get('hours', '')

    # Log what data we received for debugging
    logger.info(f"AI Context Data - Site: {site_name}, Services: {len(services)}, Phone: {bool(contact_phone)}, Email: {bool(contact_email)}, About length: {len(about)}")
    logger.debug(f"Full contact data received: {contact}")

    # Validate that we have meaningful data to provide to AI
    has_meaningful_data = (
        bool(contact_phone) or
        bool(contact_email) or
        bool(contact_address) or
        len(services) > 0 or
        len(about) > 50 or
        bool(site_desc)
    )

    if not has_meaningful_data:
        logger.warning(f"AI mode: No meaningful website data available for {site_name}. AI may not be able to provide detailed answers.")

    # Feature gating: Free plan = service only, Starter/Premium = product access
    # Starter plan: limit to 10 products, Premium: unlimited (up to 30 in AI context)
    normalized_plan = user_plan.lower()

    show_products = (normalized_plan in ["starter", "premium"] and business_type == "product")
    product_limit = 10 if normalized_plan == "starter" else 30

    # Build CONTACT section FIRST (most important for service queries)
    contact_section = f"## 📞 CONTACT INFORMATION for {site_name}:\n"
    has_contact_info = False
    if contact_phone:
        contact_section += f"- Phone: {contact_phone}\n"
        has_contact_info = True
    if contact_email:
        contact_section += f"- Email: {contact_email}\n"
        has_contact_info = True
    if contact_address:
        contact_section += f"- Address: {contact_address}\n"
        has_contact_info = True
    if contact_hours:
        contact_section += f"- Business Hours: {contact_hours}\n"
        has_contact_info = True

    if not has_contact_info:
        contact_section += "- Contact information is being updated. Please ask the customer to check the website or we'll have someone reach out.\n"

    # Build ABOUT/WEBSITE section with better structure
    website_section = f"## 🌐 ABOUT {site_name}:\n"
    if site_desc:
        website_section += f"Description: {site_desc}\n\n"
    if about:
        website_section += f"About Us: {about[:800]}\n\n"

    # Services section - make it prominent
    services_section = ""
    if services and len(services) > 0:
        services_section = f"## 🛠️ OUR SERVICES:\n"
        for idx, service in enumerate(services[:15], 1):
            services_section += f"{idx}. {service}\n"
        services_section += "\n"

    website_section += f"Business Type: {business_type.upper()} based\n"
    website_section += f"User Plan: {user_plan.title()}\n"

    # Build product catalog section with plan-based limits
    catalog_section = ""
    if business_type == "product":
        if show_products and products:
            catalog_lines = ["## 🛍️ PRODUCT CATALOG:"]
            for p in products[:product_limit]:
                p_name = p.get('name', '?')[:50]
                sku = p.get('sku', '')
                price = p.get('price', '0')
                stock = "In Stock" if p.get("stock_status") == "instock" else "Out of Stock"
                catalog_lines.append(f"  - {p_name} | SKU: {sku} | {price} PKR | {stock}")
            if len(products) > product_limit:
                catalog_lines.append(f"  ...and {len(products) - product_limit} more products")
            if normalized_plan == "starter":
                catalog_lines.append("\n📦 *Note*: Starter plan shows first 10 products. Upgrade to Premium for full catalog.")
            catalog_section = "\n".join(catalog_lines)
        elif normalized_plan == "free":
            catalog_section = "## PRODUCTS: Not available in Free plan. Upgrade to Starter or Premium for product catalog access."
        else:
            catalog_section = "## PRODUCTS: No product data available. Focus on services and contact info."
    else:
        # Service mode: Products are not relevant - emphasize services
        catalog_section = "## 🛠️ SERVICE MODE: Focus on providing information about SERVICES, CONTACT DETAILS, BUSINESS HOURS, and LOCATION. No product catalog available."

    # Build system prompt: user's custom prompt + website data
    user_prompt = prompt.strip() if prompt else ""
    if not user_prompt:
        if business_type == "service":
            services_text = ", ".join(services[:10]) if services else "various professional services"
            user_prompt = (f"You are a helpful customer service assistant for {site_name}. "
                          f"Your job is to answer customer questions using the information provided below. "
                          f"We offer {services_text}. "
                          f"Always use the contact information, services, and business details provided in the sections below.")
        else:
            # Product-based business - all paid plans get product access
            user_prompt = (f"You are a helpful customer service assistant for {site_name}. "
                          f"Your job is to answer customer questions using the information provided below. "
                          f"Always use the product catalog, contact information, and business details provided in the sections below.")

    system = f"""{user_prompt}

{website_section}

{services_section}

{catalog_section}

{contact_section}

## 🎯 HOW TO RESPOND TO CUSTOMERS:

**STEP 1 - READ THE INFORMATION ABOVE FIRST:**
All the information you need is provided in the sections above (ABOUT, SERVICES, PRODUCTS, CONTACT).
Before answering ANY question, check these sections for the answer.

**STEP 2 - ANSWER USING THE PROVIDED DATA:**

When customer asks about CONTACT (phone, email, address, hours):
→ Look at ## CONTACT INFORMATION section and share those details directly
→ Example: "You can reach us at [phone from above] or email [email from above]"

When customer asks about SERVICES (what you offer, what you do):
→ Look at ## OUR SERVICES section and list the services shown there
→ Example: "We offer: [list services from above]"

When customer asks about PRODUCTS (items, prices, availability):
→ Look at ## PRODUCT CATALOG section and share matching products with prices
→ Example: "We have [product name] for [price] PKR"

When customer asks ABOUT the business (who you are, what you do):
→ Look at ## ABOUT section and summarize that information
→ Example: Use the description and about text provided above

**STEP 3 - IMPORTANT RULES:**
✓ ALWAYS use information from the sections above - it's there for you to use
✓ Keep answers SHORT (2-3 lines) - this is WhatsApp
✓ Be friendly and helpful
✓ If customer shows interest, offer to connect them with someone: "Would you like me to have someone call you?"

✗ NEVER say "I don't have that information" if it's in the sections above
✗ NEVER say "visit the website" - share the info directly
✗ NEVER make up information that's not provided above

{lang_instruction}"""

    logger.info(f"AI ({provider}) system prompt built - total length: {len(system)} chars")
    logger.info(f"AI ({provider}) user message: '{text[:50]}...'")

    cfg = PROVIDERS.get(provider, PROVIDERS["openrouter"])

    headers = {
        "Content-Type": "application/json",
        cfg["header"]: cfg["header_fmt"].format(key=api_key),
    }
    for k, v in cfg.get("extra_headers", {}).items():
        headers[k] = v

    logger.info(f"AI ({provider}) Request headers: {list(headers.keys())}")
    logger.info(f"AI ({provider}) Authorization header present: {'Authorization' in headers}")
    logger.info(f"AI ({provider}) API URL: {cfg['url']}")

    # Model selection logic
    default_models = {
        "openrouter": "openai/gpt-4o-mini",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "qwen": "qwen-plus",
    }

    # If model_name was passed (this is specific_model_name from database)
    model = model_name or default_models.get(provider, "openai/gpt-4o-mini")
    
    # Strip "models/" prefix for Gemini OpenAI-compatible endpoint if present
    if provider == "gemini" and model.startswith("models/"):
        model = model.replace("models/", "")
    
    # Safety check: if user switched provider but kept old specific_model_name
    # (e.g. provider=openai but model=gemini-2.0), fallback to default
    is_valid_for_provider = False
    if provider in AVAILABLE_MODELS:
        valid_values = [m["value"] for m in AVAILABLE_MODELS[provider]]
        if model in valid_values:
            is_valid_for_provider = True
    
    # Custom check for OpenRouter paths or direct model values
    if not is_valid_for_provider:
        if provider == "openrouter" and "/" in model:
            # Valid OpenRouter path (e.g. provider/model)
            pass
        else:
            model = default_models.get(provider, "openai/gpt-4o-mini")

    logger.info(f"AI ({provider}) final selection: model={model}")

    try:
        request_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text}
            ],
            "temperature": temperature,
            "max_tokens": 500,
            "stream": False
        }

        logger.info(f"AI ({provider}) Making request to: {cfg['url']}")
        logger.info(f"AI ({provider}) Headers being sent: {headers}")
        logger.info(f"AI ({provider}) Model: {model}")

        # Handle provider-specific payload differences if any
        if provider == "gemini" and "generativelanguage" in cfg["url"]:
            # Google Gemini OpenAI-compatible endpoint is mostly standard
            pass

        r = requests.post(cfg["url"], headers=headers, json=request_payload, timeout=12, verify=False)
        logger.info(f"AI ({provider}) API response status: {r.status_code}")
        logger.info(f"AI ({provider}) Response body: {r.text[:500]}")

        if r.status_code == 200:
            data = r.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"AI ({provider}) raw response: {reply[:100] if reply else 'EMPTY'}...")
            if reply and len(reply.strip()) > 1:
                return reply.strip()[:600]
            logger.warning(f"AI ({provider}) response was empty or too short")
        elif r.status_code == 429:
            # Rate limit exceeded
            logger.error(f"AI ({provider}) RATE LIMIT EXCEEDED: {r.text[:200] if r.text else 'No content'}")
            return "API_RATE_LIMIT_EXCEEDED"
        elif r.status_code in [402, 403]:
            # Quota exceeded or payment required
            logger.error(f"AI ({provider}) QUOTA EXCEEDED: {r.status_code} - {r.text[:200] if r.text else 'No content'}")
            return "API_QUOTA_EXCEEDED"
        elif r.status_code == 401:
            # Invalid API key
            logger.error(f"AI ({provider}) INVALID API KEY: {r.text[:200] if r.text else 'No content'}")
            return "API_INVALID_KEY"
        else:
            logger.error(f"AI ({provider}) API error: {r.status_code} - {r.text[:200] if r.text else 'No content'}")
    except requests.exceptions.Timeout:
        logger.error(f"AI ({provider}) request timeout")
        return "API_TIMEOUT"
    except Exception as e:
        logger.error(f"AI ({provider}) exception: {e}", exc_info=True)

    return None
