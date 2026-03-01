from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CODEX_BRIDGE_", extra="ignore")

    db_path: str = "./data/control_plane.db"
    oss_root: str = "./data/oss"
    bootstrap_ttl_seconds: int = 3600
    token_ttl_seconds: int = 86400


settings = Settings()
