"""El estado del grafo conserva sus tipos al pasar por la serializacion del checkpointer.

Sin Redis: se usa el mismo serializador que el AsyncRedisSaver de produccion.
"""

from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import orjson
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.checkpoint.memory import InMemorySaver

from app.agentes import checkpointer as modulo
from app.agentes.checkpointer import abrir_checkpointer_redis, serializador_estado
from app.domain.modelos import (
    DiaRutina, Ejercicio, EjercicioPlanificado, Lesion, Nivel, Perfil, Rutina,
)


def _estado() -> dict:
    uid = uuid4()
    return {
        "usuario_id": uid,
        "mensaje": "hola",
        "perfil": Perfil(usuario_id=uid, objetivo="fuerza", dias_disponibles=3,
                         equipo=["barra"], nivel=Nivel.intermedio),
        "lesiones": [Lesion(zona="hombro_derecho", severidad="moderada", activa=True),
                     Lesion(zona="rodilla", severidad="leve", activa=False)],
        "rutina": Rutina(usuario_id=uid, version=2, dias=[
            DiaRutina(nombre="Dia A", ejercicios=[
                EjercicioPlanificado(ejercicio_id="sentadilla", series=3, repeticiones="8-10",
                                     descanso_seg=90, fuentes=["guia_tecnica"])])]),
        "bloqueados": ["press_militar"],
        "ejercicios_excluidos": ["press_banca"],
        "motivo_humano": None,
        "mensajes": [HumanMessage(content="hola"), AIMessage(content="que tal")],
    }


def _ida_y_vuelta(valor):
    serde = serializador_estado()
    return serde.loads_typed(serde.dumps_typed(valor))


def test_ida_y_vuelta_conserva_los_modelos_del_estado():
    estado = _estado()
    leido = _ida_y_vuelta(estado)

    assert isinstance(leido["perfil"], Perfil)
    assert isinstance(leido["perfil"].nivel, Nivel)
    assert all(isinstance(l, Lesion) for l in leido["lesiones"])
    assert isinstance(leido["rutina"], Rutina)
    assert isinstance(leido["rutina"].dias[0], DiaRutina)
    assert isinstance(leido["rutina"].dias[0].ejercicios[0], EjercicioPlanificado)
    assert isinstance(leido["usuario_id"], UUID)
    assert isinstance(leido["mensajes"][0], HumanMessage)
    assert leido == estado


@pytest.mark.parametrize("campo", ["usuario_id", "perfil", "lesiones", "rutina"])
def test_cada_canal_por_separado_conserva_su_tipo(campo):
    # LangGraph serializa cada canal del estado por separado
    valor = _estado()[campo]
    assert _ida_y_vuelta(valor) == valor
    assert type(_ida_y_vuelta(valor)) is type(valor)


def test_el_allowlist_cubre_todos_los_modelos_del_estado():
    # derivado del esquema: un modelo nuevo en EstadoCoach queda cubierto sin tocar el serializador
    assert {Perfil, Lesion, Rutina, DiaRutina, EjercicioPlanificado} <= set(modulo.modelos_del_estado())


def test_no_revive_clases_fuera_del_allowlist():
    # el allowlist es exacto: una clase ajena al estado no se reconstruye desde Redis
    sobre = {"lc": 2, "type": "constructor", "id": ["app", "domain", "modelos", "Ejercicio"],
             "kwargs": {"id": "x", "nombre": "x", "musculo_primario": "x",
                        "musculos_secundarios": [], "equipo": "x", "nivel": "principiante",
                        "instrucciones": []}}
    serde = serializador_estado()
    leido = serde.loads_typed(("json", orjson.dumps({"x": sobre})))
    assert not isinstance(leido["x"], Ejercicio)


async def test_checkpointer_en_memoria_con_el_serializador_conserva_tipos():
    saver = InMemorySaver(serde=serializador_estado())
    estado = _estado()
    cfg = {"configurable": {"thread_id": "t", "checkpoint_ns": ""}}
    ckpt = empty_checkpoint()
    ckpt["channel_values"] = {k: v for k, v in estado.items()}
    ckpt["channel_versions"] = {k: 1 for k in estado}
    await saver.aput(cfg, ckpt, {}, ckpt["channel_versions"])
    leido = (await saver.aget_tuple(cfg)).checkpoint["channel_values"]
    assert leido == estado
    assert isinstance(leido["rutina"], Rutina)
    assert isinstance(leido["usuario_id"], UUID)


async def test_el_checkpointer_de_produccion_usa_el_serializador_del_estado(monkeypatch):
    # sin Redis: se sustituye solo la conexion; la configuracion es la de produccion
    import langgraph.checkpoint.redis.aio as aio

    from app.main import Constructores

    class SaverFalso:
        serde = None

        async def asetup(self):
            pass

    @asynccontextmanager
    async def desde_url(url):
        yield SaverFalso()

    monkeypatch.setattr(aio.AsyncRedisSaver, "from_conn_string", desde_url)
    async with Constructores().checkpointer("redis://falso:6379/0") as saver:
        assert type(saver.serde) is type(serializador_estado())
        valor = _estado()["rutina"]
        assert saver.serde.loads_typed(saver.serde.dumps_typed(valor)) == valor
    async with abrir_checkpointer_redis("redis://falso:6379/0") as saver:
        assert type(saver.serde) is type(serializador_estado())


# --- modelos leidos de Postgres (asyncpg) -------------------------------------------------

def _uuid_asyncpg(valor: UUID):
    # asyncpg devuelve las columnas uuid como asyncpg.pgproto.pgproto.UUID (subclase de
    # uuid.UUID); Pydantic lo acepta tal cual en los campos UUID de los modelos
    from asyncpg.pgproto.pgproto import UUID as UUIDAsyncpg

    return UUIDAsyncpg(str(valor))


def _estado_tras_dolor() -> dict:
    """Forma exacta del estado del escenario de dolor agudo (sistema): perfil y rutina leidos
    de Postgres y la rutina guardada tras retirar el ejercicio con dolor."""
    uid = uuid4()
    uid_bd = _uuid_asyncpg(uid)
    rutina = Rutina(usuario_id=uid_bd, version=2, dias=[
        DiaRutina(nombre="Dia 1", ejercicios=[
            EjercicioPlanificado(ejercicio_id="Dumbbell_Bicep_Curl", series=3, repeticiones="10",
                                 descanso_seg=60, fuentes=[])]),
        DiaRutina(nombre="Dia 2", ejercicios=[
            EjercicioPlanificado(ejercicio_id="Leg_Press", series=3, repeticiones="10",
                                 descanso_seg=60, fuentes=[]),
            EjercicioPlanificado(ejercicio_id="Hammer_Curls", series=3, repeticiones="10",
                                 descanso_seg=60, fuentes=[])]),
    ])
    assert type(rutina.usuario_id) is not UUID  # precondicion: el UUID de asyncpg se conserva
    return {
        "usuario_id": uid,
        "mensaje": "Dame una rutina nueva de 3 días para esta semana.",
        "perfil": Perfil(usuario_id=uid_bd, objetivo="hipertrofia", dias_disponibles=3,
                         equipo=["barbell", "dumbbell"], nivel=Nivel.intermedio),
        "lesiones": [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)],
        "rutina": rutina,
        "ejercicios_excluidos": ["Barbell_Bench_Press_-_Medium_Grip"],
    }


def test_modelos_con_uuid_de_asyncpg_vuelven_del_serializador():
    estado = _estado_tras_dolor()
    for campo in ("perfil", "rutina"):
        leido = _ida_y_vuelta(estado[campo])
        assert type(leido) is type(estado[campo]), campo
        assert leido == estado[campo]
        assert type(leido.usuario_id) is UUID
    leido = _ida_y_vuelta(estado)
    assert isinstance(leido["rutina"], Rutina)
    assert [p.ejercicio_id for d in leido["rutina"].dias for p in d.ejercicios] == [
        "Dumbbell_Bicep_Curl", "Leg_Press", "Hammer_Curls"]
    assert leido == estado


def test_un_modelo_del_allowlist_que_no_se_puede_reconstruir_falla_visiblemente():
    # p. ej. un checkpoint escrito antes del arreglo: usuario_id sin valor recuperable
    sobre = {"lc": 2, "type": "constructor", "id": ["app", "domain", "modelos", "Rutina"],
             "kwargs": {"usuario_id": {"lc": 2, "type": "constructor",
                                       "id": ["asyncpg", "pgproto", "pgproto", "UUID"],
                                       "kwargs": {}},
                        "version": 2, "dias": []}}
    serde = serializador_estado()
    with pytest.raises(modulo.ModeloNoReconstruible, match="Rutina"):
        serde.loads_typed(("json", orjson.dumps({"rutina": sobre})))


async def test_checkpointer_en_memoria_conserva_la_rutina_de_postgres():
    saver = InMemorySaver(serde=serializador_estado())
    estado = _estado_tras_dolor()
    cfg = {"configurable": {"thread_id": "t", "checkpoint_ns": ""}}
    ckpt = empty_checkpoint()
    ckpt["channel_values"] = dict(estado)
    ckpt["channel_versions"] = {k: 1 for k in estado}
    await saver.aput(cfg, ckpt, {}, ckpt["channel_versions"])
    leido = (await saver.aget_tuple(cfg)).checkpoint["channel_values"]
    assert isinstance(leido["rutina"], Rutina)
    assert isinstance(leido["perfil"], Perfil)
    assert leido == estado


@pytest.mark.integracion
async def test_redis_real_conserva_la_rutina_de_postgres_tras_retirar_un_ejercicio():
    import os

    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        async with abrir_checkpointer_redis(url):
            pass
    except Exception:
        pytest.skip("Redis no disponible")
    estado = _estado_tras_dolor()
    cfg = {"configurable": {"thread_id": f"test-ckpt-{uuid4()}", "checkpoint_ns": ""}}
    ckpt = empty_checkpoint()
    ckpt["channel_values"] = dict(estado)
    ckpt["channel_versions"] = {k: 1 for k in estado}
    async with abrir_checkpointer_redis(url) as saver:
        await saver.aput(cfg, ckpt, {}, ckpt["channel_versions"])
    async with abrir_checkpointer_redis(url) as saver:  # otra conexion: se lee de Redis
        leido = (await saver.aget_tuple(cfg)).checkpoint["channel_values"]
        await saver.adelete_thread(cfg["configurable"]["thread_id"])
    assert isinstance(leido["rutina"], Rutina)
    assert isinstance(leido["perfil"], Perfil)
    assert leido == estado


@pytest.mark.integracion
async def test_redis_real_falla_visiblemente_si_un_modelo_no_se_puede_reconstruir():
    # el AsyncRedisSaver captura cualquier error al revivir y devuelve el sobre crudo: el
    # checkpointer de produccion no puede tragarse el fallo de un modelo del estado
    import os

    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        async with abrir_checkpointer_redis(url):
            pass
    except Exception:
        pytest.skip("Redis no disponible")
    estado = _estado_tras_dolor()
    # dato guardado que ya no valida (series=0 viola ge=1): construido sin validar
    invalido = EjercicioPlanificado.model_construct(
        ejercicio_id="Leg_Press", series=0, repeticiones="10", descanso_seg=60, fuentes=[])
    estado["rutina"] = estado["rutina"].model_copy(
        update={"dias": [DiaRutina.model_construct(nombre="Dia 1", ejercicios=[invalido])]})
    cfg = {"configurable": {"thread_id": f"test-ckpt-{uuid4()}", "checkpoint_ns": ""}}
    ckpt = empty_checkpoint()
    ckpt["channel_values"] = dict(estado)
    ckpt["channel_versions"] = {k: 1 for k in estado}
    async with abrir_checkpointer_redis(url) as saver:
        await saver.aput(cfg, ckpt, {}, ckpt["channel_versions"])
    async with abrir_checkpointer_redis(url) as saver:
        try:
            with pytest.raises(modulo.ModeloNoReconstruible, match="EjercicioPlanificado"):
                await saver.aget_tuple(cfg)
        finally:
            await saver.adelete_thread(cfg["configurable"]["thread_id"])
