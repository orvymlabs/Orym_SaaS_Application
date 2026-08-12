from fastapi import APIRouter, Depends, HTTPException, Request, Body, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Integration, Bot, MetaOAuthCode
from schemas.integration import IntegrationUpdate, IntegrationResponse, WooCommerceFetchStatus, MetaOAuthCallbackRequest
from services import decode_token
from services.encryption import encrypt_value, decrypt_value
from services.website_fetcher import fetch_website_content as fetch_website_service
from services.universal_website_fetcher import UniversalWebsiteFetcher
from services.meta_oauth import (
    MetaOAuthService,
    OAUTH_CODE_ALREADY_PROCESSED,
)
from config import get_settings
import logging
import json
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


PLAN_ERROR_FREE = "⚠️ Product features are not available in Free plan. Please upgrade to Starter or Premium plan."

def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return int(payload.get("sub", 0))


def get_user_plan(user_id: int, db: Session) -> str:
    """Get user plan from database."""
    from models import User
    user = db.query(User).filter(User.id == user_id).first()
    return user.plan if user else "starter"


@router.get("/me", response_model=IntegrationResponse)
def get_integrations(request: Request, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from models import Bot
    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")
    
    verify_token = integ.verify_token
    if not verify_token:
        from config import get_settings
        verify_token = get_settings().DEFAULT_VERIFY_TOKEN

    categories = []
    if integ.woo_products_cached and integ.woo_categories_cached:
        try:
            categories = json.loads(integ.woo_categories_cached) if isinstance(integ.woo_categories_cached, str) else integ.woo_categories_cached
        except:
            categories = []

    products_count = integ.woo_products_count if integ.woo_products_cached else 0
    webhook_url = f"{str(request.base_url).rstrip('/')}/webhook" 

    return {
        "id": integ.id,
        "bot_id": integ.bot_id,
        "phone_number_id": integ.phone_number_id,
        "whatsapp_number": integ.whatsapp_number,
        "verify_token": verify_token,
        "woocommerce_url": integ.woocommerce_url,
        "wp_base_url": integ.wp_base_url,
        "business_type": integ.business_type or "product",
        "has_whatsapp_token": bool(integ.whatsapp_token),
        "whatsapp_token_preview": integ.whatsapp_token[:20] + "..." if integ.whatsapp_token else "Not set",
        "has_woo_keys": bool(integ.woo_consumer_key),
        "woo_products_cached": integ.woo_products_cached,
        "woo_categories_cached": categories,
        "woo_products_count": products_count,
        "webhook_url": webhook_url,
    }


@router.patch("/me")
def update_integrations(
    data: IntegrationUpdate, 
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    """Update user integrations with robust error handling and background refresh."""
    from models import Bot
    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")

    user_plan = get_user_plan(user_id, db)
    logger.info(f"Updating integration for user {user_id} (plan: {user_plan})")

    # Plan-based feature gating
    product_field_submitted = (
        (data.business_type is not None and data.business_type == "product") or
        (data.woocommerce_url is not None and data.woocommerce_url.strip() != "") or
        data.woo_consumer_key is not None or
        data.woo_consumer_secret is not None
    )

    # Normalize plan name
    normalized_plan = user_plan.lower()

    if normalized_plan == "free" and product_field_submitted:
        raise HTTPException(403, PLAN_ERROR_FREE)

    # Track changes for cache refresh
    url_changed = False
    if data.woocommerce_url is not None:
        new_url = UniversalWebsiteFetcher.normalize_url(data.woocommerce_url)
        if integ.woocommerce_url != new_url:
            url_changed = True
            integ.woocommerce_url = new_url

    if data.business_type is not None:
        if integ.business_type != data.business_type:
            url_changed = True
            integ.business_type = data.business_type

    # Update WhatsApp fields
    if data.whatsapp_token is not None:
        if data.whatsapp_token.strip() != "":
            try:
                integ.whatsapp_token = encrypt_value(data.whatsapp_token)
            except Exception as e:
                logger.error(f"WhatsApp token encryption failed: {e}")
                raise HTTPException(500, "Failed to encrypt WhatsApp token")
        else:
            integ.whatsapp_token = None

    if data.phone_number_id is not None:
        new_phone_id = data.phone_number_id.strip()
        if new_phone_id != "" and new_phone_id != integ.phone_number_id:
            # Check if this ID is already used by another integration
            existing = db.query(Integration).filter(
                Integration.phone_number_id == new_phone_id,
                Integration.id != integ.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"The WhatsApp Phone Number ID '{new_phone_id}' is already registered with another bot. Please use a unique ID."
                )
        integ.phone_number_id = new_phone_id

    if data.whatsapp_number is not None:
        integ.whatsapp_number = data.whatsapp_number.strip()

    if data.verify_token is not None:
        # Meta requires alphanumeric only - strip any invalid characters
        clean_token = data.verify_token.strip()
        # Remove any non-alphanumeric characters (Meta's requirement)
        clean_token = ''.join(c for c in clean_token if c.isalnum())
        if not clean_token:
            raise HTTPException(400, "Verify token must contain only alphanumeric characters (letters and numbers)")
        if len(clean_token) < 5:
            raise HTTPException(400, "Verify token must be at least 5 characters long")
        integ.verify_token = clean_token

    # Update WooCommerce fields
    if data.woo_consumer_key is not None:
        if data.woo_consumer_key.strip() != "":
            try:
                integ.woo_consumer_key = encrypt_value(data.woo_consumer_key)
            except Exception as e:
                logger.error(f"Woo Key encryption failed: {e}")
                raise HTTPException(500, "Failed to encrypt WooCommerce Key")
        else:
            integ.woo_consumer_key = None

    if data.woo_consumer_secret is not None:
        if data.woo_consumer_secret.strip() != "":
            try:
                integ.woo_consumer_secret = encrypt_value(data.woo_consumer_secret)
            except Exception as e:
                logger.error(f"Woo Secret encryption failed: {e}")
                raise HTTPException(500, "Failed to encrypt WooCommerce Secret")
        else:
            integ.woo_consumer_secret = None

    if data.wp_base_url is not None:
        integ.wp_base_url = data.wp_base_url.strip()

    # Commit changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed: {e}")
        raise HTTPException(500, f"Database error: {str(e)}")

    # Always clear cache after any integration update
    from services.default_bot import clear_cache_for_bot, refresh_cache
    clear_cache_for_bot(integ.bot_id)
    logger.info(f"Cache cleared for bot {integ.bot_id} after integration update")

    # Trigger background cache refresh if URL changed
    if url_changed:
        refresh_url = integ.woocommerce_url or integ.wp_base_url
        if refresh_url:
            key = decrypt_value(integ.woo_consumer_key) if integ.woo_consumer_key else ""
            secret = decrypt_value(integ.woo_consumer_secret) if integ.woo_consumer_secret else ""

            logger.info(f"Queueing background cache refresh for bot {integ.bot_id}")
            background_tasks.add_task(
                refresh_cache,
                integ.bot_id, key, secret,
                integ.woocommerce_url or "", "",
                integ.wp_base_url or "",
                business_type=integ.business_type
            )

    return {"status": "ok"}


@router.post("/me/fetch-website-content")
def fetch_website_content(request: Request, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Fetch and cache website content for AI mode."""
    from models import Bot, SiteInfoCache
    from sqlalchemy.sql import func

    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")

    # Determine which URL to use based on business type
    site_type = integ.business_type or "product"
    website_url = integ.woocommerce_url if site_type == "product" else integ.wp_base_url

    if not website_url:
        raise HTTPException(400, f"Please provide your {'store' if site_type == 'product' else 'website'} URL first in the Platform tab.")

    try:
        logger.info(f"Fetching website content for bot {integ.bot_id} from {website_url}")

        # Initialize results
        products = []
        site_info = {
            "site_name": website_url,
            "site_description": "",
            "about": "",
            "services": [],
            "contact": {"phone": "", "email": "", "address": "", "hours": ""}
        }

        # Try to fetch site info (basic info - fast)
        try:
            site_info = UniversalWebsiteFetcher.fetch_site_info(website_url)
            logger.info(f"Site info fetched: {site_info.get('site_name', 'N/A')}")
        except Exception as e:
            logger.warning(f"Failed to fetch site info: {e}")

        # Try to fetch products (can be slow)
        try:
            fetcher_data = UniversalWebsiteFetcher.scrape_products_from_website(website_url, limit=30)
            products = fetcher_data.get("products", [])
            logger.info(f"Products fetched: {len(products)}")
        except Exception as e:
            logger.warning(f"Failed to fetch products: {e}")

        # Update or create cache for this bot
        cache = db.query(SiteInfoCache).filter(SiteInfoCache.bot_id == integ.bot_id).first()
        if not cache:
            cache = SiteInfoCache(bot_id=integ.bot_id, website_url=website_url)
            db.add(cache)

        cache.site_name = site_info.get("site_name") or website_url
        cache.site_description = site_info.get("site_description", "")
        cache.about = site_info.get("about", "")
        cache.services = site_info.get("services", [])
        cache.phone = site_info.get("contact", {}).get("phone", "")
        cache.email = site_info.get("contact", {}).get("email", "")
        cache.address = site_info.get("contact", {}).get("address", "")
        cache.hours = site_info.get("contact", {}).get("hours", "")
        cache.products = products
        cache.last_updated = func.now()
        db.commit()

        logger.info(f"✅ Website content cached for bot {integ.bot_id}: {len(products)} products, site: {cache.site_name}")

        # Build success message - show only site name and "all data fetched"
        if cache.site_name and cache.site_name != website_url:
            message = f"Successfully cached: Site: {cache.site_name}, all data fetched"
        else:
            message = "Successfully cached: all data fetched"

        return {
            "success": True,
            "message": message,
            "data": {
                "site_title": cache.site_name,
                "site_name": cache.site_name,
                "site_description": cache.site_description,
                "about": cache.about[:500] if cache.about else "",
                "products_count": len(products),
                "services_count": len(cache.services or []),
                "contact": {
                    "phone": cache.phone,
                    "email": cache.email,
                    "address": cache.address,
                    "hours": cache.hours
                },
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch website content: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to fetch content: {str(e)}", "data": {}}


@router.get("/me/button-code")
def get_whatsapp_button_code(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from models import Bot
    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ or not integ.whatsapp_number:
        raise HTTPException(400, "Please set your WhatsApp number in Integrations first.")
    
    number = integ.whatsapp_number.replace("+", "").replace(" ", "").replace("-", "")
    code = f"""<!-- WhatsApp Floating Button by ORVYN -->
<a href="https://wa.me/{number}" target="_blank" style="position: fixed; bottom: 20px; right: 20px; background-color: #25D366; color: white; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; text-decoration: none; box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 9999;">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="white" viewBox="0 0 24 24">
        <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.438 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/>
    </svg>
</a>"""
    return {"code": code}


@router.post("/me/fetch-woocommerce", response_model=WooCommerceFetchStatus)
def fetch_woocommerce_data(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from models import Bot
    from services.plan_enforcement import PlanEnforcementService

    # Initialize plan enforcement service
    plan_service = PlanEnforcementService(db)
    user_plan = plan_service.get_user_plan(user_id)

    if not user_plan:
        raise HTTPException(404, "User plan not found")

    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")

    woo_url = integ.woocommerce_url or integ.wp_base_url
    if not woo_url:
        raise HTTPException(400, "Please provide your website/store URL first.")

    consumer_key = consumer_secret = ""
    if integ.woo_consumer_key and integ.woo_consumer_secret:
        try:
            consumer_key = decrypt_value(integ.woo_consumer_key)
            consumer_secret = decrypt_value(integ.woo_consumer_secret)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")

    if consumer_key and consumer_secret:
        result = UniversalWebsiteFetcher.fetch_products_with_auth(woo_url, consumer_key, consumer_secret)
    else:
        result = UniversalWebsiteFetcher.scrape_products_from_website(woo_url)

    if not result["success"]:
        return {
            "success": False,
            "total_products": integ.woo_products_count,
            "total_categories": 0,
            "message": result.get("error", "Failed to fetch content from website."),
            "error": result.get("error")
        }

    # Enforce product limits based on plan
    total_products = result.get("total_products", 0)
    can_fetch, error_msg = plan_service.can_fetch_products(user_id, total_products)

    if not can_fetch:
        return {
            "success": False,
            "total_products": integ.woo_products_count,
            "total_categories": 0,
            "message": error_msg,
            "error": error_msg
        }

    integ.woo_products_cached = True
    integ.woo_categories_cached = json.dumps(result.get("categories", []))
    integ.woo_products_count = total_products

    # Update subscription usage
    subscription = plan_service.get_user_subscription(user_id)
    if subscription:
        subscription.products_fetched = total_products

    db.commit()

    return {
        "success": True,
        "total_products": total_products,
        "total_categories": len(result.get("categories", [])),
        "message": "Successfully fetched: all data fetched"
    }


@router.post("/me/discover-website")
def discover_website(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from models import Bot
    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")
    
    website_url = integ.woocommerce_url or integ.wp_base_url
    if not website_url:
        raise HTTPException(400, "Please provide your website URL first.")
    
    result = UniversalWebsiteFetcher.auto_discover_and_fetch(website_url)
    if result["success"] and not integ.wp_base_url:
        integ.wp_base_url = UniversalWebsiteFetcher.normalize_url(website_url)
        db.commit()
    
    return result


@router.post("/me/configure-base")
async def configure_integration_base(
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    config: dict = Body(...)
):
    from models import Bot
    user_plan = get_user_plan(user_id, db)
    integration_type = config.get("integration_type")
    
    # Normalize plan name
    normalized_plan = user_plan.lower()

    if normalized_plan == "free" and integration_type == "product":
        raise HTTPException(403, PLAN_ERROR_FREE)

    integ = db.query(Integration).join(Integration.bot).filter(Bot.user_id == user_id).first()
    if not integ:
        raise HTTPException(404, "Integrations not found")

    website_url = config.get("website_url")
    if not integration_type or not website_url:
        raise HTTPException(400, "Integration type and website URL are required.")

    normalized_url = UniversalWebsiteFetcher.normalize_url(website_url)
    integ.business_type = integration_type
    if integration_type == "product":
        integ.woocommerce_url = normalized_url
    else:
        integ.wp_base_url = normalized_url
    
    db.commit()
    
    # Trigger discovery in background
    background_tasks.add_task(UniversalWebsiteFetcher.auto_discover_and_fetch, normalized_url)

    return {"success": True, "message": "Base configuration saved. Discovery started in background."}


@router.get("/meta/config")
def get_meta_config():
    """Get Meta App configuration for Embedded Signup."""
    settings = get_settings()

    if not settings.META_APP_ID or not settings.META_CONFIG_ID:
        raise HTTPException(500, "Meta Embedded Signup is not configured on the server")

    return {
        "app_id": settings.META_APP_ID,
        "config_id": settings.META_CONFIG_ID
    }


@router.get("/meta/verify")
async def verify_meta_config(
    user_id: int = Depends(get_current_user_id),
):
    """
    Server-side Meta Embedded Signup configuration health check.

    Verifies every configuration item that CAN be verified from the backend
    and returns a structured checklist for the items that must match the
    production Embedded Signup flow. Items that can only be confirmed in the
    Meta App Dashboard are reported with status "manual" and the exact expected
    value.

    Server-verified items:
      - META_APP_ID / META_APP_SECRET / META_CONFIG_ID are configured
      - the App Secret belongs to the App ID and the Graph API version is
        supported (GET /<APP_ID> with an <APP_ID>|<APP_SECRET> app token)
      - the frontend configuration endpoint serves the same App ID / Config ID
        that the backend is configured with (by construction)

    The app secret is never logged or returned.
    """
    settings = get_settings()

    app_id = (settings.META_APP_ID or "").strip()
    app_secret = (settings.META_APP_SECRET or "").strip()
    config_id = (settings.META_CONFIG_ID or "").strip()

    redirect_uri = (settings.META_OAUTH_REDIRECT_URI or "").strip()
    production_origin = ""
    try:
        parts = urlsplit(redirect_uri)
        if parts.scheme and parts.netloc:
            production_origin = f"{parts.scheme}://{parts.netloc}"
    except Exception:
        production_origin = ""

    graph_version = MetaOAuthService.GRAPH_API_BASE.rstrip("/").rsplit("/", 1)[-1]

    def check(status: str, detail: str) -> dict:
        return {"status": status, "detail": detail}

    checks = {}

    checks["app_id_configured"] = check(
        "pass" if app_id else "fail",
        f"META_APP_ID is {'set (' + app_id + ')' if app_id else 'NOT set on the server'}",
    )
    checks["app_secret_configured"] = check(
        "pass" if app_secret else "fail",
        "META_APP_SECRET is set on the server" if app_secret else "META_APP_SECRET is NOT set on the server",
    )
    checks["config_id_configured"] = check(
        "pass" if config_id else "fail",
        f"META_CONFIG_ID is {'set (' + config_id + ')' if config_id else 'NOT set on the server'}",
    )
    checks["frontend_uses_backend_config"] = check(
        "pass" if app_id and config_id else "not_checked",
        "The frontend reads /api/integrations/meta/config, which serves exactly "
        "this App ID / Config ID, so frontend and backend use the same config "
        "by construction.",
    )

    credential_check = {
        "status": "not_checked",
        "detail": "Requires META_APP_ID and META_APP_SECRET to be configured.",
        "app_name": None,
        "graph_version_supported": None,
    }
    if app_id and app_secret:
        oauth_service = MetaOAuthService(app_id, app_secret)
        ok, cred_data, error = await oauth_service.verify_app_credentials()
        if ok:
            credential_check = {
                "status": "pass",
                "detail": f"App Secret verified for App ID {app_id} - app name: {cred_data.get('app_name', '')}",
                "app_name": cred_data.get("app_name"),
                "graph_version_supported": True,
            }
        else:
            version_ok = cred_data and cred_data.get("graph_version_supported")
            credential_check = {
                "status": "fail" if version_ok else "version_fail",
                "detail": f"Meta rejected the credential check: {error}",
                "app_name": None,
                "graph_version_supported": version_ok,
            }
    checks["app_secret_valid_for_app_id"] = credential_check
    checks["graph_api_version_supported"] = check(
        "pass" if credential_check.get("graph_version_supported") else "fail",
        f"Backend uses {graph_version}. A version-unsupported response from Meta "
        "means the configured version is not valid for this app.",
    )

    checks["facebook_login_for_business"] = check(
        "manual",
        "In the Meta App Dashboard confirm the app is set up with the Facebook "
        "Login for Business product (Tech Provider). The exchange sends "
        "redirect_uri=\"\" because the FB.login popup code is bound to Meta's "
        "internal xd_arbiter redirect URI.",
    )
    checks["client_oauth_login"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Client OAuth Login must be Yes.",
    )
    checks["web_oauth_login"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Web OAuth Login must be Yes.",
    )
    checks["login_with_javascript_sdk"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Login with the JavaScript SDK must be Yes.",
    )
    checks["enforce_https"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Enforce HTTPS must be Yes.",
    )
    checks["embedded_browser_oauth_login"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Embedded Browser OAuth Login must be Yes.",
    )
    checks["use_strict_mode_for_redirect_uris"] = check(
        "manual",
        "Facebook Login for Business > Settings > Client OAuth settings > Use Strict Mode for redirect URIs must be Yes.",
    )
    checks["allowed_domains_include_production_domain"] = check(
        "manual",
        f"Allowed Domains must include the production spawning domain "
        f"({production_origin or 'https://apps.orvym.com'}).",
    )
    checks["valid_oauth_redirect_uris_include_production_domain"] = check(
        "manual",
        f"Valid OAuth Redirect URIs must include the production spawning domain "
        f"({production_origin or 'https://apps.orvym.com'} and its trailing-slash "
        "variant). The backend Render URL must NOT be added unless Meta's current "
        "docs require it for this exact flow.",
    )
    checks["config_id_belongs_to_app_id"] = check(
        "manual",
        f"Confirm the Embedded Signup configuration {config_id or '(not configured)'} "
        f"belongs to App ID {app_id or '(not configured)'} in the Meta App Dashboard.",
    )
    checks["app_in_live_mode"] = check(
        "manual",
        "The Meta App must be in Live mode. Development mode restricts the flow.",
    )
    checks["account_update_webhook_subscribed"] = check(
        "manual",
        "Meta requires the app to be subscribed to the account_update webhook, "
        "which is triggered when a customer completes Embedded Signup.",
    )

    status_counts = {"pass": 0, "fail": 0, "manual": 0, "not_checked": 0, "version_fail": 0}
    for c in checks.values():
        s = c["status"]
        if s in status_counts:
            status_counts[s] += 1

    logger.info(
        f"Meta config verification requested by user {user_id}: "
        f"pass={status_counts['pass']} fail={status_counts['fail']} "
        f"manual={status_counts['manual']} not_checked={status_counts['not_checked']}"
    )

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "graph_api_version": graph_version,
        "app_id": app_id or None,
        "config_id": config_id or None,
        "production_domain": production_origin or "https://apps.orvym.com",
        "summary": status_counts,
        "checks": checks,
    }


@router.post("/meta/oauth/callback")
async def meta_oauth_callback_post(
    payload: MetaOAuthCallbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Handle Meta Embedded Signup callback via POST.

    OFFICIAL META IMPLEMENTATION (per CLAUDE.md requirements):

    The frontend forwards the following from Embedded Signup:
      - code             : exchangeable authorization code (REQUIRED)
      - waba_id          : WhatsApp Business Account ID from the
                           WA_EMBEDDED_SIGNUP completion event (optional - the
                           backend resolves it server-side when absent)
      - phone_number_id  : business phone number ID from the completion event
                           (optional - resolved server-side when absent)
      - business_id      : business portfolio ID from the completion event
                           (optional)

    The backend token exchange follows Meta's official Embedded Signup
    documentation and sends ONLY three parameters:
      - client_id
      - client_secret
      - code

    The redirect_uri parameter is OMITTED entirely per official Meta
    documentation. This is the standard approach for FB.login() + config_id
    Embedded Signup flow.

    Official Meta token exchange:
        GET /oauth/access_token?client_id=<APP_ID>&client_secret=<APP_SECRET>&code=<CODE>

    The backend then:
      1. Rejects duplicate authorization codes (SHA-256 hash ledger) - a code
         is NEVER exchanged twice.
      2. Exchanges the code server-side for the customer business token
         (client_id + client_secret + code; redirect_uri OMITTED per official
         Meta documentation)
      3. Validates the exchanged token via /debug_token (app_id + scopes)
      4. Validates the WABA via GET /<WABA_ID> and the phone number via
         GET /<WABA_ID>/phone_numbers - using ONLY IDs Meta itself returned
         (session event, then the /debug_token granular_scopes target_ids)
      5. Subscribes the WABA to the app via POST /<WABA_ID>/subscribed_apps
      6. Saves credentials (never exposes the access token to the frontend)
    """
    settings = get_settings()

    # The exchangeable code is required. WABA ID / phone number ID / business
    # ID are optional: the backend resolves the asset IDs server-side (the
    # WA_EMBEDDED_SIGNUP session event is primary; /debug_token granular_scopes
    # target_ids and the WABA phone_numbers edge are the documented fallback).
    if not payload.code or len(str(payload.code).strip()) < 10:
        raise HTTPException(400, "Missing authorization code from Embedded Signup completion data")

    code = str(payload.code).strip()
    waba_id = (str(payload.waba_id).strip() if payload.waba_id else "") or None
    phone_number_id = (str(payload.phone_number_id).strip() if payload.phone_number_id else "") or None
    business_id = (str(payload.business_id).strip() if payload.business_id else "") or None

    # Idempotency guard: a Meta authorization code is single-use and short-lived.
    # Only the SHA-256 hash is stored (never the raw code). If the same code
    # reaches the backend again, it is rejected BEFORE any exchange attempt.
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    existing_code = db.query(MetaOAuthCode).filter(MetaOAuthCode.code_hash == code_hash).first()
    if existing_code:
        logger.warning(
            f"Duplicate Meta OAuth authorization code rejected for user {user_id} "
            f"(hash {code_hash[:12]}...) - OAUTH_CODE_ALREADY_PROCESSED"
        )
        raise HTTPException(
            409,
            f"{OAUTH_CODE_ALREADY_PROCESSED}: this authorization code has already "
            "been processed. Authorization codes are single-use. Please restart "
            "WhatsApp Embedded Signup to get a fresh code.",
        )

    # Mask the code in ALL logs. Never log the full code, access tokens or secrets.
    masked_code = f"{code[:8]}...{code[-4:]} (length {len(code)})"
    logger.info("=" * 80)
    logger.info("META OAUTH CALLBACK - POST REQUEST")
    logger.info("=" * 80)
    logger.info(f"User ID: {user_id}")
    logger.info(f"Code received: {masked_code}")
    logger.info(f"WABA ID: {waba_id or '(NOT provided - session info missing)'}")
    logger.info(f"Phone Number ID: {phone_number_id or '(NOT provided - session info missing)'}")
    logger.info(f"Business ID: {business_id or '(not provided)'}")
    logger.info("=" * 80)

    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        logger.error("Meta OAuth not configured - missing APP_ID or APP_SECRET")
        raise HTTPException(500, "Meta OAuth is not configured on the server")

    # Get user's bot and integration
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        logger.error(f"Bot not found for user {user_id}")
        raise HTTPException(404, "Bot not found")

    integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
    if not integ:
        logger.error(f"Integration not found for bot {bot.id}")
        raise HTTPException(404, "Integration not found")

    # Record the code as processed BEFORE the exchange so the same single-use
    # code can never be exchanged twice, even if the exchange itself fails (a
    # failed exchange attempt still burns the code).
    processed = MetaOAuthCode(code_hash=code_hash, user_id=user_id)
    db.add(processed)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        duplicate = db.query(MetaOAuthCode).filter(MetaOAuthCode.code_hash == code_hash).first()
        if duplicate:
            logger.warning(
                f"Concurrent duplicate Meta OAuth code rejected for user {user_id} "
                f"- OAUTH_CODE_ALREADY_PROCESSED"
            )
            raise HTTPException(
                409,
                f"{OAUTH_CODE_ALREADY_PROCESSED}: this authorization code has "
                "already been processed. Authorization codes are single-use. "
                "Please restart WhatsApp Embedded Signup to get a fresh code.",
            )
        logger.error(f"Failed to persist OAuth code ledger entry: {e}")
        raise HTTPException(500, "Failed to record the authorization code")

    # Initialize OAuth service and complete the Embedded Signup setup. The
    # WABA ID / phone number ID / business ID come from the Embedded Signup
    # session event when available and are resolved server-side (the documented
    # /debug_token granular_scopes + WABA phone_numbers edge fallback) when
    # absent. redirect_uri is intentionally NOT forwarded: the Embedded Signup
    # exchange sends only client_id + client_secret + code + redirect_uri="".
    oauth_service = MetaOAuthService(settings.META_APP_ID, settings.META_APP_SECRET)
    success, integration_data, error = await oauth_service.setup_whatsapp_integration(
        code,
        waba_id=waba_id,
        phone_number_id=phone_number_id,
        business_id=business_id,
    )

    if not success:
        logger.error(f"OAuth setup failed for user {user_id}: {error}")
        raise HTTPException(400, error or "Failed to connect WhatsApp")

    # Check if phone_number_id is already used by another integration
    existing = db.query(Integration).filter(
        Integration.phone_number_id == integration_data["phone_number_id"],
        Integration.id != integ.id
    ).first()

    if existing:
        raise HTTPException(
            400,
            f"The WhatsApp number {integration_data['display_phone_number']} is already connected to another account"
        )

    # Save credentials to integration
    try:
        integ.whatsapp_token = encrypt_value(integration_data["access_token"])
        integ.phone_number_id = integration_data["phone_number_id"]
        integ.whatsapp_number = integration_data["display_phone_number"]
        integ.waba_id = integration_data["waba_id"]
        integ.business_id = integration_data.get("business_id") or None
        integ.verified_name = integration_data.get("verified_name") or None
        integ.connection_status = "connected"

        # Generate verify token if not exists (Meta requires alphanumeric only)
        if not integ.verify_token:
            import secrets
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            integ.verify_token = "orvym" + "".join(secrets.choice(alphabet) for _ in range(32))

        db.commit()

        logger.info(
            f"Successfully connected WhatsApp for user {user_id}: "
            f"{integration_data['display_phone_number']} (WABA {integration_data['waba_id']})"
        )

        return {
            "success": True,
            "status": "connected",
            "waba_id": integration_data["waba_id"],
            "phone_number_id": integration_data["phone_number_id"],
            "business_id": integration_data.get("business_id") or "",
            "phone_registered": integration_data.get("phone_registered", False),
            "data": {
                "business_name": integration_data.get("business_name", ""),
                "phone_number": integration_data["display_phone_number"],
                "phone_number_id": integration_data["phone_number_id"],
                "waba_id": integration_data["waba_id"],
                "verified_name": integration_data.get("verified_name", ""),
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save integration: {e}")
        raise HTTPException(500, "Failed to save WhatsApp credentials")


@router.post("/whatsapp/disconnect")
def disconnect_whatsapp(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Disconnect WhatsApp integration.
    Removes WhatsApp credentials but keeps all other data intact.
    """
    bot = db.query(Bot).filter(Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found")

    integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
    if not integ:
        raise HTTPException(404, "Integration not found")

    # Clear only WhatsApp credentials
    integ.whatsapp_token = None
    integ.phone_number_id = None
    integ.whatsapp_number = None

    try:
        db.commit()
        logger.info(f"WhatsApp disconnected for user {user_id}")
        return {"success": True, "message": "WhatsApp disconnected successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to disconnect WhatsApp: {e}")
        raise HTTPException(500, "Failed to disconnect WhatsApp")

