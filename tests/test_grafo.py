import os
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import Field

from app.agentes.estado import AnalisisMensaje, DecisionSupervisor, PerfilParcial, PlanPropuesto
from app.agentes.grafo import LIMITE_PASOS, config_hilo, construir_grafo, ruta_seguridad
from app.agentes.nodos import AVISO_MEDICO, detectar_dolor_agudo
from app.domain.modelos import (
    DiaRutina,
    Ejercicio,
    EjercicioPlanificado,
    EntrenoRegistro,
    Lesion,
    Nivel,
    Perfil,
    Rutina,
)
from app.llm import LLMNoDisponible
from app.settings import Settings


# --- ruta_seguridad (funcion pura) --------------------------------------------

def test_plan_con_bloqueados_vuelve_al_programador_hasta_el_limite():
    estado = {"bloqueados": ["press_militar"], "intentos_seguridad": 0}
    assert ruta_seguridad(estado, max_intentos=2) == "programador"


def test_agota_reintentos_y_responde_sin_plan_seguro():
    estado = {"bloqueados": ["press_militar"], "intentos_seguridad": 2}
    assert ruta_seguridad(estado, max_intentos=2) == "sintesis"


def test_dolor_agudo_pasa_a_humano():
    estado = {"bloqueados": [], "intentos_seguridad": 0, "requiere_humano": True}
    assert ruta_seguridad(estado, max_intentos=2) == "hitl"


def test_requiere_humano_tiene_prioridad_sobre_los_reintentos():
    estado = {"bloqueados": ["press_militar"], "intentos_seguridad": 0, "requiere_humano": True}
    assert ruta_seguridad(estado, max_intentos=2) == "hitl"


def test_plan_sin_bloqueados_va_a_sintesis():
    assert ruta_seguridad({"bloqueados": [], "intentos_seguridad": 1}, max_intentos=2) == "sintesis"


# --- deteccion determinista de dolor agudo -------------------------------------

@pytest.mark.parametrize("texto", [
    "Siento un DOLOR AGUDO en el hombro",
    "me dueLe mucho la rodilla",
    "noté un pinchazo al bajar",
    "tengo un dolor fuerte en la espalda",
    "dolor agúdo en el codo",
])
def test_detecta_dolor_agudo_por_palabras_clave(texto):
    assert detectar_dolor_agudo(texto)


def test_mensaje_normal_no_es_dolor_agudo():
    assert not detectar_dolor_agudo("Quiero una rutina de 3 dias para ganar fuerza")


# --- dobles de prueba ----------------------------------------------------------

class LLMFalso(BaseChatModel):
    """Chat model falso: colas de salidas estructuradas por esquema y textos fijos."""

    estructuradas: dict[str, list] = Field(default_factory=dict)
    textos: list[str] = Field(default_factory=list)
    llamadas: list[str] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "falso"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.llamadas.append("texto")
        texto = self.textos.pop(0) if self.textos else "Respuesta del coach."
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=texto))])

    def with_structured_output(self, schema, **kwargs):
        def _salida(entrada):
            self.llamadas.append(schema.__name__)
            cola = self.estructuradas.get(schema.__name__, [])
            if not cola:
                return None
            r = cola.pop(0) if len(cola) > 1 else cola[0]
            if isinstance(r, Exception):
                raise r
            return r

        async def _asalida(entrada):
            return _salida(entrada)

        return RunnableLambda(_salida, afunc=_asalida)


class RepoFalso:
    def __init__(self):
        self.perfiles: dict[UUID, Perfil] = {}
        self.lesiones: dict[UUID, list[Lesion]] = {}
        self.rutinas: dict[UUID, list[Rutina]] = {}
        self.entrenos: dict[UUID, list[EntrenoRegistro]] = {}

    async def guardar_perfil(self, perfil):
        self.perfiles[perfil.usuario_id] = perfil

    async def obtener_perfil(self, usuario_id):
        return self.perfiles.get(usuario_id)

    async def agregar_lesion(self, usuario_id, lesion):
        self.lesiones.setdefault(usuario_id, []).append(lesion)

    async def lesiones_activas(self, usuario_id):
        return [l for l in self.lesiones.get(usuario_id, []) if l.activa]

    async def guardar_rutina(self, rutina):
        previas = self.rutinas.setdefault(rutina.usuario_id, [])
        previas.append(rutina.model_copy(update={"version": len(previas) + 1}))

    async def rutina_actual(self, usuario_id):
        previas = self.rutinas.get(usuario_id, [])
        return previas[-1] if previas else None

    async def registrar_entreno(self, entreno):
        self.entrenos.setdefault(entreno.usuario_id, []).append(entreno)

    async def historial(self, usuario_id, limite):
        return list(reversed(self.entrenos.get(usuario_id, [])))[:limite]


def _ej(id_: str, musculo: str) -> Ejercicio:
    return Ejercicio(id=id_, nombre=id_.replace("_", " "), musculo_primario=musculo,
                     musculos_secundarios=[], equipo="barra", nivel=Nivel.principiante,
                     instrucciones=[])


CATALOGO = {e.id: e for e in [
    _ej("press_militar", "hombros"),
    _ej("elevaciones_frontales", "hombros"),
    _ej("sentadilla", "cuadriceps"),
    _ej("press_banca", "pecho"),
    _ej("remo_con_barra", "espalda"),
]}


def _dias(*ids: str) -> list[DiaRutina]:
    return [DiaRutina(nombre="Dia A", ejercicios=[
        EjercicioPlanificado(ejercicio_id=i, series=3, repeticiones="8-10",
                             descanso_seg=90, fuentes=["guia_tecnica"]) for i in ids])]


def _plan(*ids: str) -> PlanPropuesto:
    return PlanPropuesto(dias=_dias(*ids), explicacion="Plan basado en la guia de tecnica.")


async def _buscador_falso(consulta, filtros):
    return []


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        qdrant_collection="c",
        google_api_key="x",
        gemini_model="x",
        gemini_rpm=600,
        phoenix_collector_endpoint="http://localhost:6006",
        embedding_model="modelo-falso",
        max_reintentos_seguridad=2,
    )


@pytest.fixture
def usuario() -> UUID:
    return uuid4()


@pytest.fixture
def repo(usuario) -> RepoFalso:
    r = RepoFalso()
    r.perfiles[usuario] = Perfil(usuario_id=usuario, objetivo="fuerza", dias_disponibles=3,
                                 equipo=["barra"], nivel=Nivel.principiante)
    return r


async def _grafo(settings, repo, llm, checkpointer=None):
    return await construir_grafo(settings, repo, checkpointer or InMemorySaver(),
                                 catalogo=CATALOGO, llm=llm, buscador=_buscador_falso)


def _ids_rutina(rutina: Rutina | None) -> set[str]:
    return {p.ejercicio_id for d in (rutina.dias if rutina else []) for p in d.ejercicios}


# --- grafo completo con LLM falso ----------------------------------------------

async def test_grafo_tiene_limite_de_pasos(settings, repo):
    grafo = await _grafo(settings, repo, LLMFalso())
    assert grafo.config["recursion_limit"] == LIMITE_PASOS


async def test_genera_rutina_segura_y_responde_con_aviso(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla", "press_banca")],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Armame una rutina"},
                                 config_hilo(usuario))
    assert "sentadilla" in salida["respuesta"]
    assert salida["respuesta"].endswith("Esto no es un diagnóstico médico.")
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla", "press_banca"}
    assert llm.llamadas.count("texto") == 0  # la sintesis del plan es determinista


async def test_plan_bloqueado_se_rehace_y_no_llega_a_la_respuesta(settings, repo, usuario):
    repo.lesiones[usuario] = [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("press_militar", "sentadilla"), _plan("sentadilla", "remo_con_barra")],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Quiero una rutina"},
                                 config_hilo(usuario))
    assert "press_militar" not in salida["respuesta"]
    assert "press militar" not in salida["respuesta"]
    assert salida["intentos_seguridad"] == 1
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla", "remo_con_barra"}


async def test_agotar_reintentos_no_entrega_plan_y_sugiere_profesional(settings, repo, usuario):
    repo.lesiones[usuario] = [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("press_militar")],  # siempre el mismo plan inseguro
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Quiero una rutina"},
                                 config_hilo(usuario))
    assert llm.llamadas.count("PlanPropuesto") == 3  # inicial + 2 reintentos
    assert "plan seguro" in salida["respuesta"]
    assert "profesional" in salida["respuesta"]
    assert "press_militar" not in salida["respuesta"]
    assert salida["respuesta"].endswith(AVISO_MEDICO)
    assert salida["rutina"] is None
    assert await repo.rutina_actual(usuario) is None


async def test_lesion_a_mitad_de_conversacion_revalida_la_rutina_existente(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
            Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "Me lesione el hombro derecho"}, config_hilo(usuario))
    actual = await repo.rutina_actual(usuario)
    assert "press_militar" not in _ids_rutina(actual)
    assert "sentadilla" in _ids_rutina(actual)
    assert actual.version == 2
    assert "press_militar" not in salida["respuesta"]
    assert "press militar" not in salida["respuesta"]
    assert "sentadilla" in salida["respuesta"]
    assert repo.lesiones[usuario][0].zona == "hombro_derecho"
    assert "DecisionSupervisor" not in llm.llamadas  # la guarda determinista decide antes del LLM


async def test_dolor_agudo_por_palabra_clave_pausa_aunque_el_llm_no_lo_marque(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(dolor_agudo=False)]})
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "Tengo un pinchazo en el pecho con el press_banca"}, cfg)
    assert "__interrupt__" in salida
    assert "DecisionSupervisor" not in llm.llamadas
    assert "PlanPropuesto" not in llm.llamadas

    final = await grafo.ainvoke(Command(resume="revisado"), cfg)
    assert "profesional" in final["respuesta"]
    assert "press_banca" in final["ejercicios_excluidos"]
    # no se generan mas recomendaciones de ese ejercicio
    assert "press_banca" not in _ids_rutina(await repo.rutina_actual(usuario))
    assert "PlanPropuesto" not in llm.llamadas


async def test_dolor_agudo_retira_el_ejercicio_de_la_rutina_antes_de_la_pausa(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "dolor agudo en el press banca"}, config_hilo(usuario))
    assert "__interrupt__" in salida
    # sin reanudar: la rutina persistida ya no lo contiene
    actual = await repo.rutina_actual(usuario)
    assert _ids_rutina(actual) == {"sentadilla"}
    assert actual.version == 2


async def test_segunda_deteccion_del_mismo_ejercicio_no_crea_otra_version(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"}, cfg)
    # la pausa se abandona y el usuario vuelve a reportar el mismo dolor
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "otra vez pinchazo con press_banca"}, cfg)
    assert "__interrupt__" in salida
    assert len(repo.rutinas[usuario]) == 2
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}


async def test_dolor_sin_ejercicio_identificable_no_toca_la_rutina(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo un dolor agudo"},
                                 config_hilo(usuario))
    assert "__interrupt__" in salida
    assert len(repo.rutinas[usuario]) == 1
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"press_banca", "sentadilla"}


async def test_ejercicio_excluido_por_dolor_no_vuelve_a_recomendarse(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca"),
                            AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("press_banca", "sentadilla"), _plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "algo raro en el press banca"}, cfg)
    assert "__interrupt__" in salida  # el LLM lo marca aunque no haya palabra clave
    await grafo.ainvoke(Command(resume="ok"), cfg)

    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Dame una rutina nueva"}, cfg)
    assert "__interrupt__" not in salida
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
    assert "press_banca" not in salida["respuesta"]


async def test_dolor_agudo_pausa_aunque_el_llm_no_este_disponible(settings, repo, usuario):
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [LLMNoDisponible("429")]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo un dolor fuerte"},
                                 config_hilo(usuario))
    assert "__interrupt__" in salida


async def test_zona_sin_regla_escala_a_humano(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
            Lesion(zona="tobillo", severidad="leve", activa=True)])],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "me torci el tobillo"}, cfg)
    assert "__interrupt__" in salida
    final = await grafo.ainvoke(Command(resume="ok"), cfg)
    assert "profesional" in final["respuesta"]


async def test_zona_sin_regla_en_programador_escala_a_humano(settings, repo, usuario):
    repo.lesiones[usuario] = [Lesion(zona="tobillo", severidad="leve", activa=True)]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    assert "__interrupt__" in salida
    assert await repo.rutina_actual(usuario) is None


async def test_pregunta_sin_plan_responde_con_aviso(settings, repo, usuario):
    llm = LLMFalso(
        estructuradas={"AnalisisMensaje": [AnalisisMensaje()],
                       "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")]},
        textos=["Solo puedo ayudarte con entrenamiento."],
    )
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "¿Quien gano el mundial?"},
                                 config_hilo(usuario))
    assert salida["respuesta"].startswith("Solo puedo ayudarte")
    assert salida["respuesta"].endswith(AVISO_MEDICO)


async def test_evaluador_crea_perfil_desde_el_mensaje(settings, usuario):
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(perfil=PerfilParcial(
            objetivo="hipertrofia", dias_disponibles=4, equipo=["barra"], nivel=Nivel.intermedio))],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    grafo = await _grafo(settings, repo, llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Entreno 4 dias con barra"},
                        config_hilo(usuario))
    assert repo.perfiles[usuario].dias_disponibles == 4


async def test_sin_perfil_no_programa(settings, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
    })
    grafo = await _grafo(settings, RepoFalso(), llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    assert "PlanPropuesto" not in llm.llamadas


async def test_mismo_thread_id_continua_el_estado_persistido(settings, repo, usuario):
    saver = InMemorySaver()
    llm = LLMFalso(
        estructuradas={"AnalisisMensaje": [AnalisisMensaje()],
                       "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")]},
        textos=["Hola.", "Seguimos."],
    )
    grafo = await _grafo(settings, repo, llm, saver)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hola"}, config_hilo(usuario))

    # "reinicio": un grafo nuevo sobre el mismo checkpointer retoma el hilo
    grafo2 = await _grafo(settings, repo, llm, saver)
    salida = await grafo2.ainvoke({"usuario_id": usuario, "mensaje": "sigo"}, config_hilo(usuario))
    assert [m.content for m in salida["mensajes"]][0] == "hola"
    assert len(salida["mensajes"]) == 4

    otro = uuid4()
    aislado = await grafo2.ainvoke({"usuario_id": otro, "mensaje": "nuevo"}, config_hilo(otro))
    assert len(aislado["mensajes"]) == 2


async def test_nodo_seguridad_falla_cerrado_ante_zona_sin_regla(repo, usuario):
    # defensa en profundidad: aunque el supervisor no la detecte, seguridad escala a humano
    from app.agentes.nodos import Nodos

    nodos = Nodos(repo, CATALOGO, LLMFalso(), _buscador_falso)
    rutina = Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla"))
    salida = await nodos.seguridad({
        "usuario_id": usuario, "rutina": rutina, "rutina_nueva": True,
        "lesiones": [Lesion(zona="tobillo", severidad="leve", activa=True)],
    })
    assert salida["requiere_humano"] is True
    assert salida["plan_validado"] is False
    assert await repo.rutina_actual(usuario) is None
    assert ruta_seguridad({**salida, "bloqueados": []}, max_intentos=2) == "hitl"


async def test_nodo_programador_falla_cerrado_ante_zona_sin_regla(repo, usuario):
    from app.agentes.nodos import Nodos

    llm = LLMFalso(estructuradas={"PlanPropuesto": [_plan("sentadilla")]})
    nodos = Nodos(repo, CATALOGO, llm, _buscador_falso)
    salida = await nodos.programador({
        "usuario_id": usuario, "mensaje": "rutina", "perfil": repo.perfiles[usuario],
        "lesiones": [Lesion(zona="tobillo", severidad="leve", activa=True)],
    })
    assert salida["requiere_humano"] is True
    assert "PlanPropuesto" not in llm.llamadas


async def test_sintesis_descarta_texto_libre_que_recomienda_un_ejercicio_bloqueado(repo, usuario):
    from app.agentes.nodos import MSG_RESPUESTA_INSEGURA, Nodos

    llm = LLMFalso(textos=["Te recomiendo hacer press militar con poco peso."])
    nodos = Nodos(repo, CATALOGO, llm, _buscador_falso)
    salida = await nodos.sintesis({
        "usuario_id": usuario, "mensaje": "¿que hago para hombros?",
        "lesiones": [Lesion(zona="hombro_derecho", severidad="leve", activa=True)],
    })
    assert "press militar" not in salida["respuesta"]
    assert salida["respuesta"] == f"{MSG_RESPUESTA_INSEGURA}\n\n{AVISO_MEDICO}"


def test_config_hilo_usa_el_usuario_como_thread_id(usuario):
    assert config_hilo(usuario)["configurable"]["thread_id"] == str(usuario)


# --- integracion con Redis -----------------------------------------------------

def _url_redis() -> str | None:
    try:
        return Settings().redis_url
    except Exception:
        return os.environ.get("REDIS_URL")


def _sin_credenciales(url: str) -> str:
    u = urlsplit(url)
    return f"{u.scheme}://{u.hostname}:{u.port}{u.path}"


@pytest.mark.integracion
async def test_checkpointer_redis_persiste_el_hilo(settings, repo, usuario):
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    url = _url_redis()
    if not url:
        pytest.skip("REDIS_URL no configurada")
    try:
        async with AsyncRedisSaver.from_conn_string(url) as saver:
            await saver.asetup()
    except Exception:
        pytest.skip(f"Redis no disponible en {_sin_credenciales(url)}")

    llm = LLMFalso(
        estructuradas={"AnalisisMensaje": [AnalisisMensaje()],
                       "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
                       "PlanPropuesto": [_plan("sentadilla")]},
    )
    async with AsyncRedisSaver.from_conn_string(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    # checkpointer reiniciado: nueva conexion, mismo thread_id
    async with AsyncRedisSaver.from_conn_string(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        estado = await grafo.aget_state(config_hilo(usuario))
        assert estado.values["mensajes"][0].content == "rutina"
        assert _ids_rutina(estado.values["rutina"]) == {"sentadilla"}
