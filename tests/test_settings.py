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

def test_falla_sin_variable_obligatoria(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "ejercicios")
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("GEMINI_RPM", "14")
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
    monkeypatch.setenv("EMBEDDING_MODEL", "modelo-test")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert [e["loc"] for e in exc_info.value.errors()] == [("database_url",)]


def test_bm25_idioma_por_defecto_y_desde_entorno(monkeypatch):
    for k, v in dict(DATABASE_URL="x", REDIS_URL="x", QDRANT_URL="x", QDRANT_COLLECTION="x", GOOGLE_API_KEY="x",
                     GEMINI_MODEL="x", GEMINI_RPM="1", PHOENIX_COLLECTOR_ENDPOINT="x", EMBEDDING_MODEL="x").items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("BM25_IDIOMA", raising=False)
    assert Settings(_env_file=None).bm25_idioma == "spanish"
    monkeypatch.setenv("BM25_IDIOMA", "english")
    assert Settings(_env_file=None).bm25_idioma == "english"
