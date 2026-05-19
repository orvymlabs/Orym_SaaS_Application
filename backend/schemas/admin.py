from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class PlanBase(BaseModel):
    plan_name: str
    display_name: str
    monthly_price: float = 0.0
    yearly_price: Optional[float] = None
    max_templates: int = 0
    max_rule_based_messages: int = 0
    max_ai_responses_per_session: int = 0
    max_products: int = 0
    website_fetch_scope: str = "homepage"
    order_form_enabled: bool = False
    multi_ai_support: bool = False
    setup_support: bool = False
    team_collaboration: bool = False
    analytics_dashboard: bool = False
    crm_integrations: bool = False
    managed_api: bool = False
    is_active: bool = True
    stripe_price_id: Optional[str] = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    display_name: Optional[str] = None
    monthly_price: Optional[float] = None
    yearly_price: Optional[float] = None
    max_templates: Optional[int] = None
    max_rule_based_messages: Optional[int] = None
    max_ai_responses_per_session: Optional[int] = None
    max_products: Optional[int] = None
    website_fetch_scope: Optional[str] = None
    order_form_enabled: Optional[bool] = None
    multi_ai_support: Optional[bool] = None
    setup_support: Optional[bool] = None
    team_collaboration: Optional[bool] = None
    analytics_dashboard: Optional[bool] = None
    crm_integrations: Optional[bool] = None
    managed_api: Optional[bool] = None
    is_active: Optional[bool] = None
    stripe_price_id: Optional[str] = None

class PlanOut(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_messages: int
    total_contacts: int
    revenue_total: float
    plan_distribution: dict
    recent_signups: List[dict]

class BroadcastCreate(BaseModel):
    title: str
    message: str
    recipients: str  # all, free, starter, growth, or specific user email
    priority: str = "normal"
