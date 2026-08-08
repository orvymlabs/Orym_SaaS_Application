from pydantic import BaseModel
from typing import Optional, List


class MetaOAuthCallbackRequest(BaseModel):
    """Request body for POST /api/integrations/meta/oauth/callback.

    The WABA ID, phone number ID and business ID returned by Meta Embedded
    Signup are the source of truth and are required for the normal FINISH flow.
    The authorization code alone must NOT be used to discover the WABA.
    """
    code: str
    redirect_uri: Optional[str] = None
    waba_id: str
    phone_number_id: str
    business_id: str


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
