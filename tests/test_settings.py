import pytest
from pydantic import ValidationError
from app.settings import Settings

def test_carga_desde_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "ejercicios")
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("GEMINI_RPM", "14")
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
    monkeypatch.setenv("EMBEDDING_MODEL", "modelo-test")
    s = Settings()
    assert s.gemini_rpm == 14
    assert s.max_reintentos_seguridad == 2

_VARIABLES = ("DATABASE_URL", "REDIS_URL", "QDRANT_URL", "QDRANT_COLLECTION", "GOOGLE_API_KEY",
              "GEMINI_MODEL", "GEMINI_RPM", "PHOENIX_COLLECTOR_ENDPOINT", "EMBEDDING_MODEL")


def test_sin_entorno_ni_env_usa_valores_por_defecto_y_sin_llm(monkeypatch):
    """Maquina limpia: sin .env ni variables la configuracion valida (arranque sin clave)."""
    for var in _VARIABLES:
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.database_url == "postgresql+asyncpg://coach:coach@localhost:5432/coach"
    assert s.qdrant_collection == "ejercicios"
    assert s.embedding_model == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    assert s.llm_configurado is False


@pytest.mark.parametrize("clave,modelo,esperado", [
    ("k", "gemini-x", True), ("", "gemini-x", False), ("k", "", False), ("  ", " ", False),
])
def test_llm_configurado_exige_clave_y_modelo(monkeypatch, clave, modelo, esperado):
    monkeypatch.setenv("GOOGLE_API_KEY", clave)
    monkeypatch.setenv("GEMINI_MODEL", modelo)
    assert Settings(_env_file=None).llm_configurado is esperado


def test_bm25_idioma_por_defecto_y_desde_entorno(monkeypatch):
    for k, v in dict(DATABASE_URL="x", REDIS_URL="x", QDRANT_URL="x", QDRANT_COLLECTION="x", GOOGLE_API_KEY="x",
                     GEMINI_MODEL="x", GEMINI_RPM="1", PHOENIX_COLLECTOR_ENDPOINT="x", EMBEDDING_MODEL="x").items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("BM25_IDIOMA", raising=False)
    assert Settings(_env_file=None).bm25_idioma == "spanish"
    monkeypatch.setenv("BM25_IDIOMA", "english")
    assert Settings(_env_file=None).bm25_idioma == "english"


def test_bm25_modelo_por_defecto_y_desde_entorno(monkeypatch):
    for k, v in dict(DATABASE_URL="x", REDIS_URL="x", QDRANT_URL="x", QDRANT_COLLECTION="x", GOOGLE_API_KEY="x",
                     GEMINI_MODEL="x", GEMINI_RPM="1", PHOENIX_COLLECTOR_ENDPOINT="x", EMBEDDING_MODEL="x").items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("BM25_MODELO", raising=False)
    assert Settings(_env_file=None).bm25_modelo == "Qdrant/bm25"
    monkeypatch.setenv("BM25_MODELO", "otro/bm25")
    assert Settings(_env_file=None).bm25_modelo == "otro/bm25"
