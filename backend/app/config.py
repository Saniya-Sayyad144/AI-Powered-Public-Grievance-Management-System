from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", enable_decoding=False)

    app_name: str = "CivicPulse AI API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://civicpulse:civicpulse@localhost:5432/civicpulse"
    jwt_secret_key: str = "replace-this-development-secret-with-at-least-32-random-characters"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = 10 * 1024 * 1024
    demo_password: str = "civicpulse-demo"
    demo_citizen_password: str | None = None
    demo_admin_password: str | None = None
    demo_officer_password: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def require_production_secret(self):
        if self.environment.casefold() not in {"development", "test"} and (len(self.jwt_secret_key) < 32 or self.jwt_secret_key.startswith("replace-")):
            raise ValueError("JWT_SECRET_KEY must be a unique random secret of at least 32 characters outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
