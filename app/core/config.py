"""Application configuration via environment variables and Secrets Manager."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MongoDB
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="painpoint")

    # Gemini
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")

    # Firecrawl
    firecrawl_api_key: str = Field(default="")

    # Scraping
    scrape_targets: str = Field(
        default="reddit.com/r/Entrepreneur,reddit.com/r/SaaS,reddit.com/r/startups,reddit.com/r/smallbusiness"
    )
    scrape_keywords: str = Field(
        default="frustrated,struggling,wish there was,problem with,how do you handle,any tool for"
    )
    scrape_post_limit: int = Field(default=50)

    # API
    cors_origins: str = Field(default="http://localhost:3000")
    admin_api_key: str = Field(default="")

    # Local dev
    local_pipeline_mode: bool = Field(default=False)

    # AWS
    aws_region: str = Field(default="us-east-1")
    aws_secrets_manager_secret_name: str = Field(default="")
    step_functions_state_machine_arn: str = Field(default="")

    @field_validator("scrape_post_limit")
    @classmethod
    def validate_post_limit(cls, v: int) -> int:
        return max(1, min(v, 500))

    @property
    def is_lambda(self) -> bool:
        import os

        return bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    @property
    def scrape_target_list(self) -> List[str]:
        return [t.strip() for t in self.scrape_targets.split(",") if t.strip()]

    @property
    def keyword_list(self) -> List[str]:
        return [k.strip() for k in self.scrape_keywords.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def apply_secrets(self, secrets: dict[str, str]) -> None:
        """Merge secrets from AWS Secrets Manager into this settings instance."""
        field_map = {
            "MONGODB_URI": "mongodb_uri",
            "MONGODB_DB_NAME": "mongodb_db_name",
            "GEMINI_API_KEY": "gemini_api_key",
            "GEMINI_MODEL": "gemini_model",
            "FIRECRAWL_API_KEY": "firecrawl_api_key",
            "SCRAPE_TARGETS": "scrape_targets",
            "SCRAPE_KEYWORDS": "scrape_keywords",
            "SCRAPE_POST_LIMIT": "scrape_post_limit",
            "CORS_ORIGINS": "cors_origins",
            "ADMIN_API_KEY": "admin_api_key",
            "STEP_FUNCTIONS_STATE_MACHINE_ARN": "step_functions_state_machine_arn",
        }
        for env_key, attr in field_map.items():
            if env_key in secrets and secrets[env_key]:
                value = secrets[env_key]
                if attr == "scrape_post_limit":
                    value = int(value)
                elif attr == "local_pipeline_mode":
                    value = str(value).lower() in ("true", "1", "yes")
                setattr(self, attr, value)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
