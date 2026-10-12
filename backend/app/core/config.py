"""Application configuration loaded from environment variables / `.env`."""

from functools import lru_cache
from typing import List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Student Test API"
    app_env: str = "development"
    debug: bool = True

    # ``DATABASE_URL`` is the canonical name. The extra aliases let deployments
    # that only expose Vercel Postgres integration variables (``POSTGRES_URL``
    # and friends) boot without duplicating the connection string.
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "POSTGRES_URL",
            "POSTGRES_PRISMA_URL",
            "POSTGRES_URL_NON_POOLING",
            "POSTGRES_URL_NO_SSL",
        ),
    )

    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"
    password_hash_algorithm: str = "argon2"

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Accept ``postgres://`` / ``postgresql://`` URLs and route them to psycopg."""
        value = (value or "").strip().strip('"').strip("'")
        if value.startswith("postgres://"):
            value = "postgresql+psycopg://" + value[len("postgres://") :]
        elif value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value[len("postgresql://") :]
        if not value:
            raise ValueError(
                "Database URL is not configured. Set the DATABASE_URL environment "
                "variable to your PostgreSQL connection string (on Vercel: Project "
                "Settings -> Environment Variables), then redeploy."
            )
        return value

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
