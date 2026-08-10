from pydantic import BaseModel
from typing import Optional, List


class MetaOAuthCallbackRequest(BaseModel):
    """Request body for POST /api/integrations/meta/oauth/callback.

    All fields are optional at the Pydantic layer so a request that is missing
    Embedded Signup data produces a structured 400 (with a useful detail
    message) instead of a generic 422. The endpoint explicitly validates the
    required fields (code and redirect_uri) before processing.

    The exchangeable code and the redirect_uri are required. redirect_uri must
    be the canonical production value (https://apps.orvym.com/dashboard/integrations/)
    - never empty, never null - because Meta's code exchange fails with
    error_subcode 36008 when redirect_uri is omitted or differs from the dialog
    request. The WABA ID and phone number ID come from the WA_EMBEDDED_SIGNUP
    completion event (captured on the frontend) and are REQUIRED by the
    backend - the Embedded Signup session is the source of truth. The backend
    NEVER discovers or guesses missing IDs; it returns a controlled
    WABA_NOT_RETURNED / PHONE_NUMBER_NOT_RETURNED error when they are absent.
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
