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
