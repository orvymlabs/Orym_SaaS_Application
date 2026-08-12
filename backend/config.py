"""Configuration settings with PostgreSQL and multi-environment support."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationInfo
from functools import lru_cache

# Get the backend directory for stable DB paths
BACKEND_DIR = Path(__file__).parent.resolve()
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """
    Production-ready settings for WhatsApp Bot SaaS Platform.

    Environment variable precedence:
    1. Direct environment variables
    2. backend/.env file
    3. Default values
    """

    # ===========================================
    # Environment
    # ===========================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    APP_NAME: str = "WhatsApp Bot SaaS Platform"

    # ===========================================
    # Allowed Origins for CORS
    # ===========================================
    ALLOWED_ORIGINS: str = ""

    # ===========================================
    # Database (PostgreSQL for Production)
    # ===========================================
    DATABASE_URL: str = ""
    POSTGRES_URL: str = ""

    # ===========================================
    # JWT Authentication
    # ===========================================
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ===========================================
    # Encryption for API keys (MUST be 32 bytes)
    # ===========================================
    ENCRYPTION_KEY: str = "32-byte-encryption-key-change-me!!"

    # ===========================================
    # Default Bot Fallback (Optional)
    # Used when user hasn't configured their own credentials
    # Consumer key/secret are OPTIONAL - some users add different website types
    # ===========================================
    DEFAULT_VERIFY_TOKEN: str = "whatsapp_bot_verify_token_123"
    DEFAULT_OPENROUTER_KEY: str = ""
    DEFAULT_WC_KEY: str = ""
    DEFAULT_WC_SECRET: str = ""
    DEFAULT_WC_URL: str = "https://hiveworks-me.com"

    # ===========================================
    # Meta WhatsApp
    # ===========================================
    META_APP_ID: str = ""  # Your Meta App ID for Embedded Signup
    META_APP_SECRET: str = "" # REQUIRED: Your Meta App Secret for webhook signature verification
    META_CONFIG_ID: str = ""  # Your Meta Configuration ID for Embedded Signup
    META_OAUTH_REDIRECT_URI: str = "https://apps.orvym.com/dashboard/integrations/"  # Frontend spawn domain for dashboard/verify display. IMPORTANT: For the Embedded Signup FB.login + config_id popup flow, the token exchange sends redirect_uri="" (EMPTY STRING) - the code is bound to Meta's internal xd_arbiter redirect URI. Omitting the parameter or sending a real URL triggers Meta error subcode 36008 (proven in production).
    META_PHONE_REGISTRATION_PIN: str = ""  # 6-digit two-step verification PIN set server-side on the customer's business phone number (POST /<PHONE_NUMBER_ID>/register). NEVER exposed to the frontend and NEVER logged.

    # ===========================================
    # Stripe Payment Processing
    # ===========================================
    STRIPE_SECRET_KEY: str = ""  # Your Stripe secret key (sk_test_... or sk_live_...)
    STRIPE_PUBLISHABLE_KEY: str = ""  # Your Stripe publishable key (pk_test_... or pk_live_...)
    STRIPE_WEBHOOK_SECRET: str = ""  # Stripe webhook signing secret (whsec_...)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def set_default_db(cls, v: str, info: ValidationInfo) -> str:
        """
        Set default database URL with PostgreSQL priority.

        Precedence:
        1. POSTGRES_URL if set (env or info.data)
        2. DATABASE_URL if set (env or info.data)
        3. SQLite fallback for development ONLY
        """
        env_postgres = os.environ.get("POSTGRES_URL")
        data_postgres = info.data.get("POSTGRES_URL")
        
        env_db = os.environ.get("DATABASE_URL")
        data_db = v or data_postgres or env_postgres or env_db
        
        db_url = data_postgres or env_postgres or env_db or data_db

        if not db_url or db_url.strip() == "":
            if info.data.get("ENVIRONMENT") == "production":
                # Do NOT default to SQLite in production. 
                # Return empty string and let database.py raise the error.
                return ""
            # SQLite fallback for development
            return f"sqlite:///{DATA_DIR / 'saas_bot.db'}"

        # SQLAlchemy requires postgresql:// instead of postgres://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        return db_url

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Warn if using default secret key in production."""
        if info.data.get("ENVIRONMENT") == "production" and v == "your-super-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "SECURITY WARNING: Using default SECRET_KEY in production! "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v

    @field_validator("ENCRYPTION_KEY", mode="before")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Ensure encryption key is exactly 32 bytes for Fernet compatibility."""
        if len(v) != 32:
            import base64
            import hashlib
            # Derive a valid 32-byte key from any length input
            return base64.urlsafe_b64encode(
                hashlib.sha256(v.encode()).digest()
            ).decode()
        return v

    class Config:
        # Load from backend/.env only
        env_file = str(BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
