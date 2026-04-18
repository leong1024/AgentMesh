"""Environment-backed settings."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    research_a2a_url: str = Field(default="http://127.0.0.1:8001")
    critic_a2a_url: str = Field(default="http://127.0.0.1:8002")
    synthesizer_a2a_url: str = Field(default="http://127.0.0.1:8003")

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated origins for CORS",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8080

    http_timeout_seconds: float = 600.0

    static_dir: str | None = Field(
        default=None,
        alias="STATIC_DIR",
        description="If set, serve SPA static files from this directory.",
    )

    @field_validator("static_dir", mode="before")
    @classmethod
    def _empty_static_none(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return str(v)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
