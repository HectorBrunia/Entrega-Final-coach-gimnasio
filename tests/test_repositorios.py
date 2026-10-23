import pytest
from uuid import uuid4
from app.persistencia.repositorios import RepositorioDominio
from app.domain.modelos import Perfil, Nivel

pytestmark = pytest.mark.integracion

@pytest.mark.asyncio
async def test_guardar_y_obtener_perfil(sesion_factory):
    repo = RepositorioDominio(sesion_factory)
    uid = uuid4()
    await repo.guardar_perfil(Perfil(usuario_id=uid, objetivo="masa", dias_disponibles=4,
                                     equipo=["mancuernas"], nivel=Nivel.principiante))
    perfil = await repo.obtener_perfil(uid)
    assert perfil is not None and perfil.dias_disponibles == 4


@pytest.mark.asyncio
async def test_crear_usuario_devuelve_id_nuevo_y_permite_usarlo(sesion_factory):
    repo = RepositorioDominio(sesion_factory)
    a, b = await repo.crear_usuario(), await repo.crear_usuario()
    assert a != b
    assert await repo.obtener_perfil(a) is None
    await repo.guardar_perfil(Perfil(usuario_id=a, objetivo="masa", dias_disponibles=3,
                                     equipo=[], nivel=Nivel.intermedio))
    assert (await repo.obtener_perfil(a)).dias_disponibles == 3


@pytest.mark.asyncio
async def test_actualizar_severidad_lesion_no_crea_filas(sesion_factory):
    from app.domain.modelos import Lesion

    repo = RepositorioDominio(sesion_factory)
    uid = await repo.crear_usuario()
    otro = await repo.crear_usuario()
    await repo.agregar_lesion(uid, Lesion(zona="hombro_derecho", severidad="moderada", activa=True))
    await repo.agregar_lesion(uid, Lesion(zona="rodilla_derecha", severidad="leve", activa=True))
    await repo.agregar_lesion(otro, Lesion(zona="hombro_derecho", severidad="leve", activa=True))
    await repo.actualizar_severidad_lesion(uid, "hombro_derecho", "grave")
    assert await repo.lesiones_activas(uid) == [
        Lesion(zona="hombro_derecho", severidad="grave", activa=True),
        Lesion(zona="rodilla_derecha", severidad="leve", activa=True),
    ]
    assert await repo.lesiones_activas(otro) == [
        Lesion(zona="hombro_derecho", severidad="leve", activa=True)]


@pytest.mark.asyncio
async def test_exclusiones_por_dolor_idempotentes_y_por_usuario(sesion_factory):
    repo = RepositorioDominio(sesion_factory)
    uid, otro = await repo.crear_usuario(), await repo.crear_usuario()
    assert await repo.exclusiones_activas(uid) == []
    await repo.agregar_exclusion(uid, "Barbell_Bench_Press_-_Medium_Grip")
    await repo.agregar_exclusion(uid, "Barbell_Bench_Press_-_Medium_Grip")  # idempotente
    await repo.agregar_exclusion(uid, "Leg_Press")
    await repo.agregar_exclusion(otro, "Hammer_Curls")
    assert await repo.exclusiones_activas(uid) == ["Barbell_Bench_Press_-_Medium_Grip", "Leg_Press"]
    assert await repo.exclusiones_activas(otro) == ["Hammer_Curls"]


@pytest.mark.asyncio
async def test_migracion_exclusiones_dolor_baja_y_sube(sesion_factory):
    import os
    import subprocess
    import sys
    from pathlib import Path

    from sqlalchemy import text

    from tests.guarda_bd import resolver_url_pruebas

    url, _ = resolver_url_pruebas(os.environ)
    raiz = Path(__file__).resolve().parent.parent

    def alembic(*args: str) -> None:
        r = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=raiz,
                           capture_output=True, text=True, env={**os.environ, "DATABASE_URL": url})
        assert r.returncode == 0, r.stderr

    async def existe() -> bool:
        async with sesion_factory() as s:
            return bool(await s.scalar(text("SELECT to_regclass('public.exclusiones_dolor') IS NOT NULL")))

    assert await existe()
    alembic("downgrade", "0001")
    assert not await existe()
    alembic("upgrade", "head")
    assert await existe()
