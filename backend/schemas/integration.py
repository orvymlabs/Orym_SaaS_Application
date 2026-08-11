from pydantic import BaseModel
from typing import Optional, List


class MetaOAuthCallbackRequest(BaseModel):
    """Request body for POST /api/integrations/meta/oauth/callback.

    All fields are optional at the Pydantic layer so a request that is missing
    Embedded Signup data produces a structured 400 (with a useful detail
    message) instead of a generic 422. The endpoint explicitly validates the
    required fields (code) before processing.

    The exchangeable code is required. redirect_uri is optional and kept only
    for backward compatibility with the deployed frontend - the Embedded
    Signup token exchange NEVER sends redirect_uri to Meta (the documented
    Meta Tech Provider exchange uses ONLY client_id + client_secret + code).
    The WABA ID and phone number ID come from the WA_EMBEDDED_SIGNUP completion
    event (captured on the frontend) when delivered; when absent the backend
    resolves them server-side using the documented Meta fallback (/debug_token
    granular_scopes target_ids + the WABA phone_numbers edge) and returns a
    controlled WABA_NOT_RETURNED / PHONE_NUMBER_NOT_RETURNED error when nothing
    can be resolved.
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
