"""
OpenClaw Lite Configuration

Lightweight API-only deployment settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    version: str = "1.0.0"
    environment: str = "production"
    port: int = 8080
    log_level: str = "INFO"

    # API Keys (from environment/secrets)
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Model Configuration
    openai_model: str = "gpt-4o-mini"  # Cheap, fast for simple queries
    claude_model: str = "claude-sonnet-4-20250514"  # Powerful for complex queries

    # Routing Configuration
    complexity_threshold: float = 0.5  # Score >= this uses Claude

    # Rate Limiting
    rate_limit_requests: int = 100  # Requests per minute
    rate_limit_window: int = 60  # Window in seconds

    # Cost Tracking
    monthly_budget_usd: float = 50.0

    # Security
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
