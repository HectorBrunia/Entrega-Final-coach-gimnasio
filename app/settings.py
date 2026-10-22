from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    qdrant_url: str
    qdrant_collection: str
    google_api_key: SecretStr
    gemini_model: str
    gemini_rpm: int
    phoenix_collector_endpoint: str
    max_reintentos_seguridad: int = 2
    embedding_model: str
    bm25_idioma: str = "spanish"
    catalogo_path: Path = Path("data/catalogo/exercises.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()
