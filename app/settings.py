from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion leida del entorno y de .env (si existe).

    Todo lo que no es secreto tiene un valor por defecto (el de .env.example, para ejecutar en
    local con el stack de docker compose), asi la app arranca en una maquina limpia sin .env.
    La clave y el modelo de Gemini son opcionales: sin ellos la API arranca igual (salud,
    usuarios, entrenos, perfil y rutinas funcionan) y /chat y /hitl responden 503 explicando
    que falta configurarlos (ver `llm_configurado`).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://coach:coach@localhost:5432/coach"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ejercicios"
    google_api_key: SecretStr = SecretStr("")
    gemini_model: str = ""
    gemini_rpm: int = 14
    phoenix_collector_endpoint: str = "http://localhost:6006/v1/traces"
    max_reintentos_seguridad: int = 2
    llm_reintentos: int = 3
    llm_espera_base: float = 2.0
    llm_espera_max: float = 20.0
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    bm25_modelo: str = "Qdrant/bm25"
    bm25_idioma: str = "spanish"
    catalogo_path: Path = Path("data/catalogo/exercises.json")
    guias_dir: Path = Path("data/guias")

    @property
    def llm_configurado(self) -> bool:
        """True si hay clave y modelo de Gemini (valores no vacios)."""
        return bool(self.google_api_key.get_secret_value().strip() and self.gemini_model.strip())


class SettingsSinLLM(Settings):
    """Settings para scripts que no llaman al LLM (ingesta, migraciones, evaluacion de recuperacion).

    Se mantiene por compatibilidad: desde que la clave y el modelo de Gemini son opcionales en
    `Settings`, es equivalente a ella.
    """


@lru_cache
def get_settings() -> Settings:
    return Settings()
