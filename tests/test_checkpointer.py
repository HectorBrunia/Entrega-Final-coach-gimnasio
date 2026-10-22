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
