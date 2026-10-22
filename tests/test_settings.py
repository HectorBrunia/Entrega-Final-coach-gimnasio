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
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
