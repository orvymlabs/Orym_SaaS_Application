from pydantic import BaseModel
from typing import Optional, List


class MetaOAuthCallbackRequest(BaseModel):
    """Request body for POST /api/integrations/meta/oauth/callback.

    All fields are optional at the Pydantic layer so a request that is missing
    Embedded Signup data produces a structured 400 (with a useful detail
    message) instead of a generic 422. The endpoint explicitly validates the
    required field (code) before processing.

    The exchangeable code is required. WABA ID / phone number ID / business ID
    are optional: the backend resolves the asset IDs server-side when absent
    (WA_EMBEDDED_SIGNUP session event first, then the /debug_token
    granular_scopes target_ids + the WABA phone_numbers edge).

    redirect_uri: the exact URL (origin + path) of the page that spawned the
    FB.login() Embedded Signup popup, e.g. https://apps.orvym.com/dashboard/integrations/
    in production or the ngrok URL when testing locally through a tunnel.
    Meta's Valid OAuth Redirect URIs app-dashboard setting is a pre-registered
    list of exactly such page URLs, and the token exchange must send the same
    value that was current when the code was issued - a fixed hardcoded
    value breaks whenever the flow is spawned from a different registered
    domain (e.g. local ngrok testing vs production).
    """
    code: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_id: Optional[str] = None
    redirect_uri: Optional[str] = None


class IntegrationUpdate(BaseModel):
    whatsapp_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    verify_token: Optional[str] = None
    woocommerce_url: Optional[str] = None
    woo_consumer_key: Optional[str] = None
    woo_consumer_secret: Optional[str] = None
    wp_base_url: Optional[str] = None
    business_type: Optional[str] = None  # No default - only check when explicitly provided


class IntegrationResponse(BaseModel):
    id: int
    bot_id: int
    phone_number_id: Optional[str]
    whatsapp_number: Optional[str] = None
    verify_token: Optional[str]
    woocommerce_url: Optional[str]
    wp_base_url: Optional[str]
    business_type: str
    has_whatsapp_token: bool
    has_woo_keys: bool
    woo_products_cached: bool
    woo_categories_cached: List[str]
    woo_products_count: int

    class Config:
        from_attributes = True


class WooCommerceFetchStatus(BaseModel):
    success: bool
    total_products: int
    total_categories: int
    message: str
    error: Optional[str] = None
