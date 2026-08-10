from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # super_admin, admin, user
    plan = Column(String(20), default="free")  # free, starter, premium (deprecated - use subscription)
    full_name = Column(String(100), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True, unique=True)  # Stripe Customer ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bot = relationship("Bot", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(50), nullable=False)
    monthly_price = Column(Float, default=0.0)
    yearly_price = Column(Float, nullable=True)

    # Legacy column for backward compatibility
    daily_message_limit = Column(Integer, default=0)

    # Conversation limits
    max_templates = Column(Integer, default=0)
    max_rule_based_messages = Column(Integer, default=0)
    max_ai_responses_per_session = Column(Integer, default=0)

    # Data & Integration limits
    max_products = Column(Integer, default=0)
    website_fetch_scope = Column(String(20), default="homepage")

    # Features
    order_form_enabled = Column(Boolean, default=False)
    multi_ai_support = Column(Boolean, default=False)
    setup_support = Column(Boolean, default=False)
    team_collaboration = Column(Boolean, default=False)
    analytics_dashboard = Column(Boolean, default=False)
    crm_integrations = Column(Boolean, default=False)
    managed_api = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    stripe_price_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    # Stripe integration
    stripe_subscription_id = Column(String(100), unique=True, nullable=True)  # Stripe Subscription ID
    stripe_price_id = Column(String(100), nullable=True)  # Current price ID

    # Subscription status
    status = Column(String(20), default="active")  # active, canceled, past_due, trialing, incomplete

    # Billing
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    # Trial
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking (reset monthly)
    templates_used = Column(Integer, default=0)
    rule_messages_used = Column(Integer, default=0)
    ai_responses_used = Column(Integer, default=0)
    products_fetched = Column(Integer, default=0)
    usage_reset_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")


class Bot(Base) :
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    mode = Column(String(20), default="default")  # default, predefined, ai
    status = Column(Boolean, default=True)  # True=active, False=stopped
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="bot")
    settings = relationship("BotSettings", back_populates="bot", uselist=False, cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="bot", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="bot", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="bot", cascade="all, delete-orphan")


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), unique=True, nullable=False)
    prompt = Column(Text, nullable=True)
    model_name = Column(String(50), default="openrouter")  # Provider: openai, gemini, openrouter, qwen
    specific_model_name = Column(String(100), nullable=True) # Exact model: gpt-4o, etc.
    api_key = Column(Text, nullable=True)  # Encrypted
    temperature = Column(Integer, default=70)
    language = Column(String(20), default="english")
    custom_responses = Column(JSON, nullable=True)
    custom_products = Column(JSON, nullable=True)
    templates = Column(JSON, nullable=True)
    template_enabled = Column(Boolean, default=True)
    template_statuses = Column(JSON, nullable=True)
    order_form_template = Column(Text, nullable=True)
    order_confirmation_message = Column(Text, nullable=True)
    order_form_enabled = Column(Boolean, default=True)
    form_menu_label = Column(String(30), nullable=True)  # Custom label for form in WhatsApp menu
    welcome_message = Column(Text, nullable=True)  # Dynamic welcome/greeting message
    response_delay = Column(Integer, default=0)  # Delay in seconds before bot responds (0 = instant)
    fallback_message = Column(Text, nullable=True)  # Message when no template matches user input
    order_error_message = Column(Text, nullable=True)  # Message when order saving fails
    error_message = Column(Text, nullable=True)  # General error message for technical issues
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bot = relationship("Bot", back_populates="settings")


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), unique=True, nullable=False)
    whatsapp_token = Column(Text, nullable=True)  # Encrypted
    phone_number_id = Column(String(100), unique=True, index=True, nullable=True)
    whatsapp_number = Column(String(30), nullable=True)  # For wa.me link generation
    verify_token = Column(String(100), nullable=True)  # Encrypted
    woocommerce_url = Column(String(255), nullable=True)  # WooCommerce store URL
    woo_consumer_key = Column(Text, nullable=True)  # Encrypted
    woo_consumer_secret = Column(Text, nullable=True)  # Encrypted
    wp_base_url = Column(String(255), nullable=True)
    woo_products_cached = Column(Boolean, default=False)  # Whether products have been fetched
    woo_categories_cached = Column(JSON, nullable=True)  # Cached category list
    woo_products_count = Column(Integer, default=0)  # Number of cached products
    business_type = Column(String(20), default="product")  # product, service
    waba_id = Column(String(100), index=True, nullable=True)  # WhatsApp Business Account ID (from Embedded Signup)
    business_id = Column(String(100), nullable=True)  # Meta business portfolio ID (from Embedded Signup)
    verified_name = Column(String(255), nullable=True)  # Verified display name from the WABA phone number
    connection_status = Column(String(50), nullable=True)  # connected, disconnected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bot = relationship("Bot", back_populates="integrations")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # "user" or "bot"
    phone_number = Column(String(30), nullable=False, index=True)
    message = Column(Text, nullable=True)
    whatsapp_message_id = Column(String(100), nullable=True, index=True)  # WhatsApp API message ID
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    seen = Column(Boolean, default=False)  # Whether the message has been seen/read

    bot = relationship("Bot", back_populates="messages")


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("bot_id", "phone", name="uq_bot_phone"),
    )

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    phone = Column(String(30), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    last_message = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)  # To store session state (step, language, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bot = relationship("Bot", back_populates="leads")


class Usage(Base):
    __tablename__ = "usage_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    whatsapp_messages_sent = Column(Integer, default=0)
    whatsapp_limit = Column(Integer, default=1000)
    ai_requests_made = Column(Integer, default=0)
    ai_limit = Column(Integer, default=500)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class SiteInfoCache(Base):
    __tablename__ = "site_info_cache"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), unique=True, nullable=False)
    website_url = Column(String(255), nullable=False)
    site_name = Column(String(255), nullable=True)
    site_description = Column(Text, nullable=True)
    about = Column(Text, nullable=True)
    services = Column(JSON, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    hours = Column(String(255), nullable=True)
    products = Column(JSON, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bot = relationship("Bot")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Customer details
    name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=False)
    address = Column(Text, nullable=True)

    # Order details
    product_name = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1)
    order_details = Column(Text, nullable=True)  # Raw filled form from customer

    # Order status
    status = Column(String(20), default="Pending")  # Pending, Completed, Cancelled

    # Metadata
    source = Column(String(50), default="default_mode")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bot = relationship("Bot", back_populates="orders")
    user = relationship("User")


class UserTemplate(Base):
    __tablename__ = "user_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # new_order, new_lead, bot_error, plan_expiry, payment_failed
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)  # user, plan, setting, etc.
    target_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MetaOAuthCode(Base):
    """
    Idempotency ledger for Meta Embedded Signup authorization codes.

    Stores a SHA-256 HASH of each processed authorization code (never the raw
    code itself). If the same single-use code reaches the backend again the
    request is rejected as a duplicate and the code is NEVER exchanged twice.
    """
    __tablename__ = "meta_oauth_codes"

    id = Column(Integer, primary_key=True, index=True)
    code_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(30), default="processed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Add back-populates to Bot model
Bot.orders = relationship("Order", back_populates="bot", cascade="all, delete-orphan")

