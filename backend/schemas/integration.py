from pydantic import BaseModel
from typing import Optional, List


class MetaOAuthCallbackRequest(BaseModel):
    """Request body for POST /api/integrations/meta/oauth/callback.

    All fields are optional at the Pydantic layer so a request that is missing
    Embedded Signup data produces a structured 400 (with a useful detail
    message) instead of a generic 422. The endpoint explicitly validates the
    required field (code) before processing.

    Only the exchangeable code is required. The WABA ID, phone number ID and
    business ID come from the WA_EMBEDDED_SIGNUP completion event (captured on
    the frontend); when they are not present the backend resolves them
    server-side from the token after the exchange. redirect_uri is sent as
    null for the FB.login popup flow (no redirect, so the exchange must omit
    it) and is only forwarded for legacy manual-dialog codes.
    """
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_id: Optional[str] = None


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
