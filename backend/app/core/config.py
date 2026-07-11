from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Meower"
    version: str = "0.1.0"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/meower.db"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    fanar_api_key: str = ""
    fanar_base_url: str = "https://api.fanar.qa/v1"
    fanar_model: str = "Fanar-C-2-27B"
    fanar_timeout: int = 120

    cors_origins: list[str] = ["*"]

    log_level: str = "INFO"

    frontend_dir: str = str(Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist")


settings = Settings()
