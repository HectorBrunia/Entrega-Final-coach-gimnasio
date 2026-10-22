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
    bm25_modelo: str = "Qdrant/bm25"
    bm25_idioma: str = "spanish"
    catalogo_path: Path = Path("data/catalogo/exercises.json")
    guias_dir: Path = Path("data/guias")


class SettingsSinLLM(Settings):
    """Settings para scripts que no llaman al LLM (ingesta, evaluacion de recuperacion).

    Lee lo mismo que `Settings` (entorno y .env), pero no exige la clave ni el modelo de
    Gemini: la ingesta y la recuperacion solo usan Qdrant y los codificadores locales.
    """

    google_api_key: SecretStr = SecretStr("")
    gemini_model: str = ""
    gemini_rpm: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
