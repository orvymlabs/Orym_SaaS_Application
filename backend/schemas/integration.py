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

    redirect_uri is intentionally NOT part of this payload. The Embedded
    Signup FB.login popup code is bound to Meta's INTERNAL redirect URI, so the
    backend token exchange sends ONLY client_id + client_secret + code - never
    redirect_uri (sending it triggers Meta error_subcode 36008). Any
    redirect_uri value in the request body is ignored by the endpoint.
    """
    code: Optional[str] = None
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
