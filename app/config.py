from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    debug: bool = Field(default=True, alias="DEBUG")

    database_url: str = Field(
        default="mysql+pymysql://bill_tracker:changeme@localhost:3306/bill_tracker",
        alias="DATABASE_URL",
    )

    congress_api_key: str = Field(default="", alias="CONGRESS_API_KEY")
    govinfo_api_key: str = Field(default="", alias="GOVINFO_API_KEY")

    lda_api_key: str = Field(default="", alias="LDA_API_KEY")
    lda_api_base_url: str = Field(default="https://lda.senate.gov/api/v1/", alias="LDA_API_BASE_URL")

    ai_provider: str = Field(default="", alias="AI_PROVIDER")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")

    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")

    default_congress: int = 119


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
