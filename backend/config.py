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
    PORT: int = 8000
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
    META_APP_SECRET: str = "" # REQUIRED: Your Meta App Secret for webhook signature verification

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def set_default_db(cls, v: str, info: ValidationInfo) -> str:
        """
        Set default database URL with PostgreSQL priority.

        Precedence:
        1. POSTGRES_URL if set
        2. DATABASE_URL if set
        3. SQLite fallback for development
        """
        postgres_url = info.data.get("POSTGRES_URL")
        db_url = postgres_url or v

        if not db_url or db_url.strip() == "":
            # SQLite fallback for development
            return f"sqlite:///{DATA_DIR / 'saas_bot.db'}"

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
