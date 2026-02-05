"""
OpenClaw Lite Configuration

Lightweight API-only deployment settings.
"""

import logging
import sys

from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _fetch_aws_secret(secret_name: str) -> str | None:
    """Fetch a secret value from AWS Secrets Manager.

    Returns None on any failure (missing boto3, no credentials, etc.).
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return None

    try:
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except (ClientError, Exception):
        return None


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

    def model_post_init(self, __context) -> None:
        if not self.openai_api_key or self.openai_api_key == "your-openai-key-here":
            secret = _fetch_aws_secret("openclaw-lite/openai-api-key")
            if secret:
                self.openai_api_key = secret
                logger.info("Loaded openai_api_key from AWS Secrets Manager")

        if not self.anthropic_api_key or self.anthropic_api_key == "your-anthropic-key-here":
            secret = _fetch_aws_secret("openclaw-lite/anthropic-api-key")
            if secret:
                self.anthropic_api_key = secret
                logger.info("Loaded anthropic_api_key from AWS Secrets Manager")


settings = Settings()
