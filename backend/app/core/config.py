import os
import sys
import json
import secrets
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database (REQUIRED - no default with credentials)
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security (REQUIRED - no insecure default)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # DeepSeek (Default LLM Provider)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # OpenAI (Optional)
    OPENAI_API_KEY: str = ""

    # Anthropic (Optional)
    ANTHROPIC_API_KEY: str = ""

    # Default LLM Configuration
    DEFAULT_LLM_PROVIDER: str = "deepseek"
    DEFAULT_LLM_MODEL: str = "deepseek-chat"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PROFESSIONAL: str = ""

    # Sentry
    SENTRY_DSN: str = ""

    # S3 / Local Storage
    S3_BUCKET: str = "zkvalue-reports"
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./storage"

    # Blockchain Anchoring (Optional — simulation mode if not configured)
    BLOCKCHAIN_RPC_URL: str = ""  # e.g., https://polygon-rpc.com
    BLOCKCHAIN_PRIVATE_KEY: str = ""
    BLOCKCHAIN_CONTRACT_ADDRESS: str = ""

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # App
    APP_NAME: str = "ZKValue"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")

    def validate_required(self) -> None:
        """Validate that all required settings are configured. Called at startup."""
        errors = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        if not self.SECRET_KEY:
            errors.append("SECRET_KEY is required (min 32 characters)")
        elif len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")
        if self.ENVIRONMENT == "production":
            if not self.DEEPSEEK_API_KEY and not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                errors.append("At least one LLM API key is required in production")
            if not self.STRIPE_SECRET_KEY:
                errors.append("STRIPE_SECRET_KEY is required in production")
            if not self.STRIPE_WEBHOOK_SECRET:
                errors.append("STRIPE_WEBHOOK_SECRET is required in production")
            if not self.SENTRY_DSN:
                print("WARNING: SENTRY_DSN not configured — error tracking disabled", file=sys.stderr)
            cors_origins = json.loads(self.CORS_ORIGINS) if self.CORS_ORIGINS else []
            for origin in cors_origins:
                if "localhost" in origin or "127.0.0.1" in origin:
                    errors.append(f"CORS_ORIGINS contains localhost in production: {origin}")
        if errors:
            print("FATAL: Configuration errors:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def generate_secret_key() -> str:
        """Helper to generate a secure secret key."""
        return secrets.token_urlsafe(48)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
