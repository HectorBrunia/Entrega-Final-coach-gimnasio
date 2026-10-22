import asyncio
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker

RAIZ = Path(__file__).resolve().parent.parent


def _url_sin_credenciales(url: str) -> str:
    u = make_url(url)
    return f"{u.drivername}://{u.host}:{u.port}/{u.database}"


# --- Persistencia (Postgres) -------------------------------------------------

@pytest_asyncio.fixture
async def sesion_factory():
    from app.persistencia.repositorios import crear_motor
    from app.persistencia.tablas import Base
    from app.settings import Settings

    try:
        url = Settings().database_url
    except Exception:
        pytest.skip("Postgres no disponible: DATABASE_URL no configurada")

    motor = crear_motor(url)
    try:
        async with motor.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await motor.dispose()
        pytest.skip(f"Postgres no disponible en {_url_sin_credenciales(url)}")

    resultado = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        await motor.dispose()
        pytest.fail(f"alembic upgrade head fallo:\n{resultado.stderr}")

    yield async_sessionmaker(motor, expire_on_commit=False)

    async with motor.begin() as conn:
        tablas = ", ".join(t.name for t in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
    await motor.dispose()
