import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from tests.guarda_bd import resolver_url_pruebas, url_sin_credenciales

RAIZ = Path(__file__).resolve().parent.parent


# --- Persistencia (Postgres) -------------------------------------------------

@pytest_asyncio.fixture
async def sesion_factory():
    from app.persistencia.repositorios import crear_motor
    from app.persistencia.tablas import Base

    url, motivo = resolver_url_pruebas(os.environ)
    if url is None:
        pytest.skip(motivo)

    motor = crear_motor(url)
    try:
        async with motor.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await motor.dispose()
        pytest.skip(f"Postgres no disponible en {url_sin_credenciales(url)}")

    resultado = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, capture_output=True, text=True,
        env={**os.environ, "DATABASE_URL": url},
    )
    if resultado.returncode != 0:
        await motor.dispose()
        pytest.fail(f"alembic upgrade head fallo:\n{resultado.stderr}")

    yield async_sessionmaker(motor, expire_on_commit=False)

    async with motor.begin() as conn:
        tablas = ", ".join(t.name for t in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
    await motor.dispose()


# --- RAG (Qdrant en memoria + codificadores deterministas) --------------------

import re as _re
import zlib as _zlib
import uuid as _uuid

from qdrant_client import AsyncQdrantClient

from app.settings import Settings

_DIM = 16


def _tokens(texto: str) -> list[str]:
    return _re.findall(r"\w+", texto.lower())


class DensoFalso:
    """Embedding determinista por hashing de tokens; registra el hilo de ejecucion."""

    def __init__(self):
        self.hilos: list[int] = []

    def codificar(self, textos: list[str]) -> list[list[float]]:
        import threading

        self.hilos.append(threading.get_ident())
        salida = []
        for t in textos:
            v = [0.0] * _DIM
            for tok in _tokens(t):
                v[_zlib.crc32(tok.encode()) % _DIM] += 1.0
            if not any(v):
                v[0] = 1.0
            salida.append(v)
        return salida

    codificar_consulta = codificar


class DisperoFalso:
    def codificar(self, textos: list[str]):
        from qdrant_client.models import SparseVector

        salida = []
        for t in textos:
            conteo: dict[int, float] = {}
            for tok in _tokens(t):
                i = _zlib.crc32(tok.encode())
                conteo[i] = conteo.get(i, 0.0) + 1.0
            idx = sorted(conteo)
            salida.append(SparseVector(indices=idx, values=[conteo[i] for i in idx]))
        return salida

    codificar_consulta = codificar


@pytest.fixture
def settings_rag() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        qdrant_collection=f"test_{_uuid.uuid4().hex[:8]}",
        google_api_key="x",
        gemini_model="x",
        gemini_rpm=1,
        phoenix_collector_endpoint="http://localhost:6006",
        embedding_model="modelo-falso",
    )


@pytest.fixture
def denso_falso() -> DensoFalso:
    return DensoFalso()


@pytest_asyncio.fixture
async def cliente_qdrant():
    cliente = AsyncQdrantClient(location=":memory:")
    yield cliente
    await cliente.close()


@pytest_asyncio.fixture
async def coleccion_prueba(cliente_qdrant, settings_rag, denso_falso):
    """Ingiere el catalogo de muestra en una coleccion en memoria y devuelve kwargs de inyeccion."""
    from app.catalogo.cargador import cargar_catalogo
    from app.rag.ingesta import documento_desde_ejercicio, ingerir

    inyeccion = dict(cliente=cliente_qdrant, denso=denso_falso, disperso=DisperoFalso())
    docs = [documento_desde_ejercicio(e) for e in cargar_catalogo(RAIZ / "tests/fixtures/catalogo_muestra.json")]
    await ingerir(docs, settings_rag, **inyeccion)
    yield inyeccion
    await cliente_qdrant.delete_collection(settings_rag.qdrant_collection)
