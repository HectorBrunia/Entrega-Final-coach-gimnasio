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
