from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PocketSmart AI"
    app_env: str = "development"

    secret_key: str = "change-this-secret-key"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    database_url: str = "sqlite:///./pocketsmart.db"

    access_token_expire_minutes: int = 1440

    max_upload_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()