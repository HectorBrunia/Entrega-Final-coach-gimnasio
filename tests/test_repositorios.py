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
