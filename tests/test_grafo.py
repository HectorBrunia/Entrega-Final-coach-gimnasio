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

from app.agentes.checkpointer import abrir_checkpointer_redis, serializador_estado
from app.agentes.estado import (
    AnalisisMensaje, DecisionSupervisor, LesionReportada, PerfilParcial, PlanPropuesto,
)
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
    entradas: list = Field(default_factory=list)  # (esquema, mensajes) de cada salida estructurada

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
            self.entradas.append((schema.__name__, entrada))
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
        self.exclusiones: dict[UUID, list[str]] = {}

    async def guardar_perfil(self, perfil):
        self.perfiles[perfil.usuario_id] = perfil

    async def obtener_perfil(self, usuario_id):
        return self.perfiles.get(usuario_id)

    async def agregar_lesion(self, usuario_id, lesion):
        self.lesiones.setdefault(usuario_id, []).append(lesion)

    async def lesiones_activas(self, usuario_id):
        return [l for l in self.lesiones.get(usuario_id, []) if l.activa]

    async def agregar_exclusion(self, usuario_id, ejercicio_id):
        actuales = self.exclusiones.setdefault(usuario_id, [])
        if ejercicio_id not in actuales:
            actuales.append(ejercicio_id)

    async def exclusiones_activas(self, usuario_id):
        return list(self.exclusiones.get(usuario_id, []))

    async def actualizar_severidad_lesion(self, usuario_id, zona, severidad):
        self.lesiones[usuario_id] = [
            l.model_copy(update={"severidad": severidad}) if l.activa and l.zona == zona else l
            for l in self.lesiones.get(usuario_id, [])
        ]

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
                     musculos_secundarios=[], equipo="barbell", nivel=Nivel.principiante,
                     instrucciones=[])


CATALOGO = {e.id: e for e in [
    _ej("press_militar", "shoulders"),
    _ej("elevaciones_frontales", "shoulders"),
    _ej("sentadilla", "quadriceps"),
    _ej("press_banca", "chest"),
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


def _saver() -> InMemorySaver:
    # mismo serializador que el checkpointer de Redis: el estado se serializa de verdad
    return InMemorySaver(serde=serializador_estado())


async def _grafo(settings, repo, llm, checkpointer=None):
    return await construir_grafo(settings, repo, checkpointer or _saver(),
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
        "AnalisisMensaje": [AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca",
                                            cita_dolor="algo raro en el press banca"),
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
            LesionReportada(zona="otra", descripcion="tobillo", severidad="leve")])],
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
    saver = _saver()
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


async def test_dos_turnos_con_checkpointer_serializador_conservan_los_tipos(settings, repo, usuario):
    # turno 1 genera la rutina; turno 2 pausa por dolor; la reanudacion lee del checkpoint
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("press_banca", "sentadilla")],
    })
    saver = _saver()
    cfg = config_hilo(usuario)
    grafo = await _grafo(settings, repo, llm, saver)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Armame una rutina"}, cfg)

    valores = (await grafo.aget_state(cfg)).values
    assert isinstance(valores["usuario_id"], UUID)
    assert isinstance(valores["perfil"], Perfil)
    assert isinstance(valores["rutina"], Rutina)
    assert _ids_rutina(valores["rutina"]) == {"press_banca", "sentadilla"}

    # "reinicio": grafo nuevo sobre el mismo checkpointer
    grafo = await _grafo(settings, repo, llm, saver)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"}, cfg)
    assert "__interrupt__" in salida
    final = await grafo.ainvoke(Command(resume="revisado"), cfg)
    assert isinstance(final["usuario_id"], UUID)
    assert isinstance(final["rutina"], Rutina)
    assert _ids_rutina(final["rutina"]) == {"sentadilla"}
    assert "profesional" in final["respuesta"]


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
    url = _url_redis()
    if not url:
        pytest.skip("REDIS_URL no configurada")
    try:
        async with abrir_checkpointer_redis(url):
            pass
    except Exception:
        pytest.skip(f"Redis no disponible en {_sin_credenciales(url)}")

    llm = LLMFalso(
        estructuradas={"AnalisisMensaje": [AnalisisMensaje()],
                       "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
                       "PlanPropuesto": [_plan("sentadilla")]},
    )
    async with abrir_checkpointer_redis(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    # checkpointer reiniciado: nueva conexion, mismo thread_id
    async with abrir_checkpointer_redis(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        estado = await grafo.aget_state(config_hilo(usuario))
        assert estado.values["mensajes"][0].content == "rutina"
        assert isinstance(estado.values["usuario_id"], UUID)
        assert isinstance(estado.values["perfil"], Perfil)
        assert isinstance(estado.values["rutina"], Rutina)
        assert _ids_rutina(estado.values["rutina"]) == {"sentadilla"}


@pytest.mark.integracion
async def test_checkpointer_redis_reanuda_la_pausa_en_otra_conexion(settings, repo, usuario):
    # la pausa HITL se reanuda con el estado leido de Redis (tipos intactos)
    url = _url_redis()
    if not url:
        pytest.skip("REDIS_URL no configurada")
    try:
        async with abrir_checkpointer_redis(url):
            pass
    except Exception:
        pytest.skip(f"Redis no disponible en {_sin_credenciales(url)}")

    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    async with abrir_checkpointer_redis(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        salida = await grafo.ainvoke(
            {"usuario_id": usuario, "mensaje": "pinchazo con press_banca"}, config_hilo(usuario))
        assert "__interrupt__" in salida
    async with abrir_checkpointer_redis(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        final = await grafo.ainvoke(Command(resume="revisado"), config_hilo(usuario))
    assert isinstance(final["usuario_id"], UUID)
    assert isinstance(final["rutina"], Rutina)
    assert _ids_rutina(final["rutina"]) == {"sentadilla"}



# --- I1: /chat sobre un hilo en pausa (grafo compilado + LLM falso + checkpointer) -------

def _cliente_api(grafo, repo):
    from httpx import ASGITransport, AsyncClient

    from app.main import crear_app

    app = crear_app(grafo=grafo, repo=repo, catalogo=CATALOGO)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")


async def _pausa_chat_409_y_reanudar(grafo, repo, usuario, llm):
    uid = str(usuario)
    async with _cliente_api(grafo, repo) as c:
        r = await c.post("/chat", json={"usuario_id": uid,
                                        "mensaje": "pinchazo con press_banca"})
        assert r.status_code == 200 and r.json()["requiere_humano"] is True

        r = await c.post("/chat", json={"usuario_id": uid, "mensaje": "dame una rutina"})
        assert r.status_code == 409
        assert f"/hitl/{uid}/reanudar" in r.json()["detail"]
        # la pausa sigue pendiente: no se llamo ni al supervisor ni al programador
        assert "DecisionSupervisor" not in llm.llamadas
        assert "PlanPropuesto" not in llm.llamadas
        assert (await grafo.aget_state(config_hilo(usuario))).interrupts

        r = await c.get(f"/usuarios/{uid}/rutinas/actual")
        assert r.status_code == 409 and "revisión" in r.json()["detail"]

        r = await c.post(f"/hitl/{uid}/reanudar", json={"revision": "revisado"})
        assert r.status_code == 200
        assert "profesional" in r.json()["respuesta"]
        assert r.json()["requiere_humano"] is False

        r = await c.get(f"/usuarios/{uid}/rutinas/actual")
        assert r.status_code == 200
        assert {p["ejercicio_id"] for d in r.json()["dias"] for p in d["ejercicios"]} == {"sentadilla"}


async def test_chat_en_pausa_devuelve_409_y_la_pausa_sigue_reanudable(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    await _pausa_chat_409_y_reanudar(grafo, repo, usuario, llm)


# --- I2: lesion nueva en un turno que escala a HITL --------------------------------------

async def test_lesion_nueva_y_dolor_agudo_en_el_mismo_mensaje_depura_antes_de_la_pausa(
    settings, repo, usuario
):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla", "press_banca")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])]})
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje":
                                  "me lesione el hombro derecho y tengo dolor agudo en el press banca"},
                                 cfg)
    assert "__interrupt__" in salida
    # sin reanudar: la rutina guardada ya no tiene lo que bloquea el hombro (ni el del dolor)
    actual = await repo.rutina_actual(usuario)
    assert _ids_rutina(actual) == {"sentadilla"}
    assert actual.version == 2

    final = await grafo.ainvoke(Command(resume="revisado"), cfg)
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
    assert len(repo.rutinas[usuario]) == 2  # idempotente: la reanudacion no crea otra version
    assert "press militar" not in final["respuesta"].lower()


async def test_zona_conocida_y_zona_sin_regla_depura_la_conocida_antes_de_la_pausa(
    settings, repo, usuario
):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        Lesion(zona="hombro_derecho", severidad="moderada", activa=True),
        LesionReportada(zona="otra", descripcion="tobillo", severidad="leve")])]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hombro y tobillo lesionados"},
                                 config_hilo(usuario))
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["motivo"] == "zona_sin_regla"
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}


async def test_zona_sin_regla_get_rutina_409_mientras_la_pausa_esta_pendiente(
    settings, repo, usuario
):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        LesionReportada(zona="otra", descripcion="tobillo", severidad="leve")])]})
    grafo = await _grafo(settings, repo, llm)
    async with _cliente_api(grafo, repo) as c:
        r = await c.post("/chat", json={"usuario_id": str(usuario), "mensaje": "tengo una lesion en el tobillo"})
        assert r.json()["requiere_humano"] is True
        assert "dolor agudo" not in r.json()["respuesta"]
        r = await c.get(f"/usuarios/{usuario}/rutinas/actual")
        assert r.status_code == 409


# --- M-c: nunca se guarda ni se muestra una rutina vacia ----------------------------------

async def test_rutina_totalmente_bloqueada_no_se_guarda_vacia(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "elevaciones_frontales")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
            Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])],
        "PlanPropuesto": [_plan("press_militar")],  # el programador insiste en algo bloqueado
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "me lesione el hombro"},
                                 config_hilo(usuario))
    assert all(_ids_rutina(r) for r in repo.rutinas[usuario])  # ninguna version vacia
    assert len(repo.rutinas[usuario]) == 1
    assert "plan seguro" in salida["respuesta"] and "profesional" in salida["respuesta"]
    assert "Tu rutina" not in salida["respuesta"]
    assert salida["respuesta"].endswith(AVISO_MEDICO)
    # la version vigente (insegura) no se sirve por la API
    async with _cliente_api(grafo, repo) as c:
        r = await c.get(f"/usuarios/{usuario}/rutinas/actual")
    assert r.status_code == 409
    assert "press_militar" not in r.text


async def test_sintesis_nunca_muestra_una_rutina_vacia(repo, usuario):
    from app.agentes.nodos import MSG_SIN_PLAN_SEGURO, Nodos

    nodos = Nodos(repo, CATALOGO, LLMFalso(), _buscador_falso)
    salida = await nodos.sintesis({
        "usuario_id": usuario, "mensaje": "rutina", "plan_validado": True,
        "rutina": Rutina(usuario_id=usuario, version=3, dias=[]),
    })
    assert salida["respuesta"] == f"{MSG_SIN_PLAN_SEGURO}\n\n{AVISO_MEDICO}"
    assert salida["rutina"] is None


async def test_plan_sin_ejercicios_no_se_guarda(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [PlanPropuesto(dias=[DiaRutina(nombre="A", ejercicios=[])])],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    assert await repo.rutina_actual(usuario) is None
    assert "Tu rutina" not in salida["respuesta"]


# --- M-b: el mensaje de HITL depende del motivo -------------------------------------------

async def test_escalado_del_supervisor_sin_dolor_no_dice_dolor_agudo(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="hitl")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo la tension alta, puedo entrenar?"}, cfg)
    assert salida["__interrupt__"][0].value["motivo"] == "escalado_supervisor"
    final = await grafo.ainvoke(Command(resume="ok"), cfg)
    assert "dolor agudo" not in final["respuesta"].lower()
    assert "profesional" in final["respuesta"]
    assert final["respuesta"].endswith(AVISO_MEDICO)


# --- I8: volumen semanal en la respuesta del programador ---------------------------------

async def test_rutina_nueva_incluye_volumen_semanal_por_musculo(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [PlanPropuesto(dias=_dias("sentadilla", "press_banca") + [
            DiaRutina(nombre="Dia B", ejercicios=[EjercicioPlanificado(
                ejercicio_id="sentadilla", series=4, repeticiones="5", descanso_seg=120,
                fuentes=[])])])],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "rutina"}, config_hilo(usuario))
    assert salida["volumen"] == {"quadriceps": 7, "chest": 3}
    assert "Volumen semanal (series por músculo principal): quadriceps 7, chest 3." in salida["respuesta"]
    assert llm.llamadas.count("texto") == 0  # determinista, sin llamada extra al LLM


async def test_revalidar_rutina_existente_no_muestra_volumen_obsoleto(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "me lesione el hombro"},
                                 config_hilo(usuario))
    assert "Retiré 1 ejercicio" in salida["respuesta"]
    assert "Volumen semanal" not in salida["respuesta"]


# --- I1 con Redis real -------------------------------------------------------------------

@pytest.mark.integracion
async def test_chat_en_pausa_con_redis_devuelve_409_y_reanuda(settings, repo, usuario):
    url = _url_redis()
    if not url:
        pytest.skip("REDIS_URL no configurada")
    try:
        async with abrir_checkpointer_redis(url):
            pass
    except Exception:
        pytest.skip(f"Redis no disponible en {_sin_credenciales(url)}")

    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    async with abrir_checkpointer_redis(url) as saver:
        grafo = await _grafo(settings, repo, llm, saver)
        await _pausa_chat_409_y_reanudar(grafo, repo, usuario, llm)


# --- dolor: solo el del mensaje actual (regla A prima) -------------------------------------

async def _pausa_por_dolor_y_reanuda(settings, repo, usuario, *siguientes: AnalisisMensaje):
    """Turno 1: dolor con press_banca -> pausa -> reanudar. Devuelve grafo, llm y cfg."""
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca",
                                            cita_dolor="pinchazo con press_banca"),
                            *(siguientes or [AnalisisMensaje()])],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"}, cfg)
    assert "__interrupt__" in salida
    await grafo.ainvoke(Command(resume="revisado"), cfg)
    assert not (await grafo.aget_state(cfg)).interrupts
    return grafo, llm, cfg


@pytest.mark.parametrize("texto", [
    "me está doliendo la rodilla",
    "me dolía",
    "estoy adolorido",
    "sentí un tirón",
    "me arde el hombro",
    "Me duele bastante",
    "dolor muy fuerte",
    "me sigue doliendo",
    "tengo molestias en el codo",
    "noto calambres en el gemelo",
    "me hice daño en la muñeca",
    "no puedo mover el brazo",
    "se me durmió la mano",
    "siento una punzada",
    "noté un pinchazo",
])
def test_senal_de_dolor_en_el_mensaje(texto):
    assert detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", [
    "Dame una rutina nueva de 3 días para esta semana.",
    "Quiero ganar fuerza con barra",
    "registra mi entreno de ayer por la tarde",
    "tengo 100 dolares para equipo",
    "Ayer me lesioné el hombro derecho",  # una lesion va por la ruta de lesiones, no por HITL
])
def test_sin_senal_de_dolor(texto):
    assert not detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", [
    "me está doliendo la rodilla", "me dolía", "estoy adolorido", "sentí un tirón",
    "me arde el hombro",
])
async def test_senal_de_dolor_escala_sin_que_el_llm_lo_marque(settings, repo, usuario, texto):
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": texto}, config_hilo(usuario))
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["motivo"] == "dolor_agudo"
    assert "DecisionSupervisor" not in llm.llamadas


async def test_dolor_del_llm_con_cita_del_mensaje_actual_escala(settings, repo, usuario):
    # sin palabras del lexico: solo el LLM lo detecta, y su cita esta en el mensaje actual
    mensaje = "Noto algo raro en el hombro al empujar en la sentadilla"
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(
        dolor_agudo=True, ejercicio_con_dolor="sentadilla",
        cita_dolor="algo raro en el HOMBRO al empujar")]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": mensaje}, config_hilo(usuario))
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["ejercicio"] == "sentadilla"


async def test_dolor_del_llm_citando_el_historial_no_escala(settings, repo, usuario, caplog):
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(
        settings, repo, usuario,
        AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca",
                        cita_dolor="pinchazo con press_banca"))
    with caplog.at_level("INFO"):
        salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Quiero entrenar fuerza"}, cfg)
    assert "__interrupt__" not in salida
    assert salida["requiere_humano"] is False
    assert "historial" in caplog.text


async def test_dolor_del_llm_sin_cita_no_escala(settings, repo, usuario):
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(
        settings, repo, usuario, AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="sentadilla"))
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Quiero entrenar fuerza"}, cfg)
    assert "__interrupt__" not in salida


async def test_escenario_original_dolor_pausa_reanuda_y_rutina_nueva_no_pausa(settings, repo, usuario):
    # el LLM falso vuelve a marcar el dolor del turno anterior (lo lee del historial)
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(
        settings, repo, usuario,
        AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca",
                        cita_dolor="pinchazo con press_banca"))
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "Dame una rutina nueva de 3 días para esta semana."}, cfg)
    assert "__interrupt__" not in salida
    assert salida["requiere_humano"] is False
    assert salida["motivo_humano"] is None
    assert salida["ejercicios_excluidos"] == ["press_banca"]
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}


async def test_dolor_de_nuevo_sobre_un_ejercicio_ya_excluido_vuelve_a_pausar(settings, repo, usuario):
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(settings, repo, usuario, AnalisisMensaje())
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "me sigue doliendo con el press banca"}, cfg)
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["ejercicio"] == "press_banca"


async def test_dolor_del_llm_con_cita_sobre_un_ejercicio_ya_excluido_vuelve_a_pausar(
    settings, repo, usuario
):
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(
        settings, repo, usuario,
        AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="press_banca",
                        cita_dolor="otra vez raro el press banca"))
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "Otra vez raro el press banca"}, cfg)
    assert "__interrupt__" in salida


async def test_dolor_en_otro_ejercicio_tras_reanudar_vuelve_a_pausar(settings, repo, usuario):
    grafo, llm, cfg = await _pausa_por_dolor_y_reanuda(
        settings, repo, usuario,
        AnalisisMensaje(dolor_agudo=True, ejercicio_con_dolor="sentadilla",
                        cita_dolor="algo raro me pasa en la sentadilla"))
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "algo raro me pasa en la sentadilla"}, cfg)
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["ejercicio"] == "sentadilla"
    assert "sentadilla" in (await grafo.aget_state(cfg)).values["ejercicios_excluidos"]


def test_prompt_del_evaluador_limita_dolor_y_lesiones_al_mensaje_actual(repo, usuario):
    from app.agentes.nodos import Nodos

    nodos = Nodos(repo, CATALOGO, LLMFalso(), _buscador_falso)
    sistema = nodos._prompt_evaluador(
        {"usuario_id": usuario, "mensaje": "hola", "mensajes": []}, None,
        [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])[0].content
    assert "solo del ultimo mensaje" in sistema.lower()
    assert "cita_dolor" in sistema
    assert "hombro_derecho" in sistema
    for campo in ("dolor_agudo", "ejercicio_con_dolor", "lesiones_nuevas", "cita_dolor"):
        assert "mensaje actual" in AnalisisMensaje.model_fields[campo].description.lower()


# --- lesiones: misma zona actualiza severidad (regla D) y zonas acotadas (regla C) ---------

async def test_lesion_repetida_en_la_misma_zona_no_se_duplica(settings, repo, usuario):
    hombro = LesionReportada(zona="hombro_derecho", severidad="moderada")
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[hombro]),
                            AnalisisMensaje(lesiones_nuevas=[hombro])],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "me lesione el hombro derecho"}, cfg)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Dame una rutina nueva"}, cfg)
    assert len(repo.lesiones[usuario]) == 1
    assert salida["lesion_nueva"] is False
    assert "DecisionSupervisor" in llm.llamadas  # no se fuerza la revalidacion por "lesion nueva"


async def test_lesion_en_la_misma_zona_con_otra_severidad_actualiza_la_existente(
    settings, repo, usuario
):
    repo.lesiones[usuario] = [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
            LesionReportada(zona="hombro_derecho", severidad="grave")])],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "la lesion del hombro derecho ahora es grave"},
        config_hilo(usuario))
    assert repo.lesiones[usuario] == [Lesion(zona="hombro_derecho", severidad="grave", activa=True)]
    assert salida["lesiones"] == repo.lesiones[usuario]


def test_la_zona_de_la_lesion_reportada_esta_acotada():
    from pydantic import ValidationError

    from app.safety.reglas import REGLAS_LESION

    for zona in [*REGLAS_LESION, "hombro", "rodilla", "otra"]:
        LesionReportada(zona=zona, severidad="leve")
    with pytest.raises(ValidationError):
        LesionReportada(zona="tobillo", severidad="leve")


async def test_hombro_sin_lado_se_guarda_en_los_dos_lados_y_bloquea_igual(settings, repo, usuario):
    from app.safety.reglas import ids_bloqueados, indice_bloqueo

    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "elevaciones_frontales",
                                                "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        LesionReportada(zona="hombro", severidad="moderada")])]})
    grafo = await _grafo(settings, repo, llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo una lesion en el hombro"},
                        config_hilo(usuario))
    assert sorted(l.zona for l in repo.lesiones[usuario]) == ["hombro_derecho", "hombro_izquierdo"]
    indice = indice_bloqueo(CATALOGO)
    derecho = ids_bloqueados([Lesion(zona="hombro_derecho", severidad="moderada", activa=True)], indice)
    izquierdo = ids_bloqueados([Lesion(zona="hombro_izquierdo", severidad="moderada", activa=True)], indice)
    assert derecho == izquierdo and derecho
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}


async def test_rodilla_sin_lado_se_guarda_en_los_dos_lados(settings, repo, usuario):
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
            LesionReportada(zona="rodilla", severidad="leve")])],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    grafo = await _grafo(settings, repo, llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo una lesion en la rodilla"},
                        config_hilo(usuario))
    assert sorted(l.zona for l in repo.lesiones[usuario]) == ["rodilla_derecha", "rodilla_izquierda"]


async def test_zona_otra_se_guarda_como_desconocida_y_escala_a_humano(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        LesionReportada(zona="otra", descripcion="cuello", severidad="moderada")])]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "tengo una lesion en el cuello"},
                                 config_hilo(usuario))
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["motivo"] == "zona_sin_regla"
    assert [l.zona for l in repo.lesiones[usuario]] == ["otra_cuello"]


# --- checkpoint irrecuperable: se reinicia el hilo y la API responde 409 (regla E) ---------

class SaverRoto(InMemorySaver):
    """Checkpointer cuyo hilo guardado no se puede reconstruir hasta que se borra."""

    def __init__(self, roto: str):
        super().__init__(serde=serializador_estado())
        self.roto: str | None = roto
        self.borrados: list[str] = []

    async def aget_tuple(self, config):
        if config["configurable"]["thread_id"] == self.roto:
            from app.agentes.checkpointer import ModeloNoReconstruible

            raise ModeloNoReconstruible("No se pudo reconstruir Rutina desde el checkpoint")
        return await super().aget_tuple(config)

    async def adelete_thread(self, thread_id):
        self.borrados.append(thread_id)
        if thread_id == self.roto:
            self.roto = None
        await super().adelete_thread(thread_id)


MSG_REINICIADA = "la conversación guardada no se pudo recuperar y se reinició"


@pytest.mark.parametrize("peticion", ["chat", "hitl", "rutina"])
async def test_hilo_irrecuperable_se_reinicia_y_responde_409(settings, repo, usuario, peticion):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla")))
    perfil = repo.perfiles[usuario]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    saver = SaverRoto(str(usuario))
    grafo = await _grafo(settings, repo, llm, saver)
    uid = str(usuario)
    async with _cliente_api(grafo, repo) as c:
        if peticion == "chat":
            r = await c.post("/chat", json={"usuario_id": uid, "mensaje": "hola"})
        elif peticion == "hitl":
            r = await c.post(f"/hitl/{uid}/reanudar", json={"revision": "ok"})
        else:
            r = await c.get(f"/usuarios/{uid}/rutinas/actual")
        assert r.status_code == 409, r.text
        assert MSG_REINICIADA in r.json()["detail"].lower()
        assert "vuelve a enviar tu mensaje" in r.json()["detail"]
        assert saver.borrados == [uid]
        # los datos de dominio (Postgres) se conservan
        assert repo.perfiles[usuario] == perfil
        assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
        # el siguiente mensaje empieza un hilo limpio
        r = await c.post("/chat", json={"usuario_id": uid, "mensaje": "hola"})
        assert r.status_code == 200, r.text


async def test_reportar_una_lesion_la_registra_y_bloquea_sin_pausa_de_dolor(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_militar", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje(lesiones_nuevas=[
        LesionReportada(zona="hombro_derecho", severidad="moderada")])]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke(
        {"usuario_id": usuario, "mensaje": "Ayer me lesioné el hombro derecho"}, config_hilo(usuario))
    assert "__interrupt__" not in salida
    assert salida["requiere_humano"] is False
    assert salida["motivo_humano"] is None
    assert [l.zona for l in repo.lesiones[usuario]] == ["hombro_derecho"]
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
    assert "press_militar" not in salida["respuesta"] and "press militar" not in salida["respuesta"]


# --- N1: lexico de lesion aguda (frases de la re-revision) y dolor en el pecho ----------------

# Frases de dolor o lesion aguda de la re-revision (fix-dolor-rutina-rereview.md): las que el
# lexico ya detectaba y las 27 que no. Todas deben escalar.
SONDA_DOLOR = [
    # detectadas antes
    "me duele", "tengo dolor", "siento una molestia", "me pincha", "no aguanto el dolor",
    "me crujió y ahora duele", "me ardió", "me arde", "ardor", "un dolor punzante", "punzadas",
    "pinchazo", "me dio un tirón", "me lastimé", "me sigue doliendo", "me dolió", "hormigueo",
    "se me durmió la mano", "no puedo mover el brazo", "calambres", "me hice daño", "adolorido",
    "MOLESTIA", "me molestaba",
    # no detectadas antes
    "me tira el gemelo", "me quema el hombro", "se me inflamó", "me torcí el tobillo",
    "sentí un chasquido en el hombro", "algo crujió en la rodilla", "me resentí",
    "me resiente el hombro", "está hinchada", "tengo la rodilla hinchada",
    "me dio un latigazo en la espalda", "me escuece", "sensación rara en el hombro",
    "me crujió la espalda y no me puedo agachar", "me fastidia la rodilla", "me jodí la espalda",
    "me rompí algo", "sentí que algo se rompió", "no puedo levantar el brazo",
    "se me salió el hombro", "me desgarré el gemelo", "tengo un desgarro", "tengo un esguince",
    "me esguincé", "la espalda me está matando", "la rodilla me está matando",
    "me cuesta respirar y me aprieta el pecho", "me mareé",
    # vocabulario de la regla N1
    "tengo el tobillo torcido", "creo que tengo una fractura", "se me luxó el hombro",
    "me disloqué el codo", "noto opresión en el pecho", "tengo el brazo entumecido",
    "se me bloqueó la espalda", "no puedo apoyar el pie", "no puedo doblar la rodilla",
    "no puedo estirar el brazo",
]

# No son dolor agudo: frases de gimnasio, lesion reportada (regla F) y agujetas (DOMS, fallo
# aceptado por la re-revision).
SONDA_SIN_DOLOR = [
    "quiero tirar más peso", "hice press con mancuernas", "sumo 5 kg", "dame una rutina",
    "Dame una rutina nueva de 3 días para esta semana.", "quiero quemar grasa",
    "rutina de pecho y espalda", "ejercicios de rotación de cadera",
    "hice 3 series de press de banca", "registra mi entreno de ayer por la tarde", "me lesioné la rodilla", "tengo agujetas",
    "tiro de cadera con barra", "estiramientos para la espalda", "tengo 100 dolares para equipo",
]


@pytest.mark.parametrize("texto", SONDA_DOLOR)
def test_sonda_de_dolor_agudo_escala(texto):
    assert detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", SONDA_SIN_DOLOR)
def test_sonda_sin_dolor_no_escala(texto):
    assert not detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", SONDA_DOLOR)
async def test_sonda_de_dolor_pausa_el_grafo_sin_flag_del_llm(settings, repo, usuario, texto):
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": texto}, config_hilo(usuario))
    assert "__interrupt__" in salida
    assert salida["__interrupt__"][0].value["motivo"] in ("dolor_agudo", "dolor_pecho")


@pytest.mark.parametrize("texto", [
    "me cuesta respirar y me aprieta el pecho", "noto opresión en el pecho",
    "me duele el pecho", "tengo un pinchazo en el pecho con el press banca",
])
def test_dolor_en_el_pecho_es_senal_de_urgencia(texto):
    from app.agentes.nodos import detectar_dolor_pecho

    assert detectar_dolor_pecho(texto)


@pytest.mark.parametrize("texto", ["rutina de pecho y espalda", "me duele la rodilla",
                                   "press de pecho con mancuernas"])
def test_pecho_sin_dolor_no_es_urgencia(texto):
    from app.agentes.nodos import detectar_dolor_pecho

    assert not detectar_dolor_pecho(texto)


async def test_dolor_en_el_pecho_pausa_con_plantilla_de_atencion_medica_inmediata(
    settings, repo, usuario
):
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    uid = str(usuario)
    async with _cliente_api(grafo, repo) as c:
        r = await c.post("/chat", json={"usuario_id": uid,
                                        "mensaje": "me cuesta respirar y me aprieta el pecho"})
        assert r.status_code == 200 and r.json()["requiere_humano"] is True
        pausa = r.json()["respuesta"].lower()
        assert "atención médica inmediata" in pausa and "112" in pausa
        assert AVISO_MEDICO.lower() in pausa
        r = await c.post(f"/hitl/{uid}/reanudar", json={"revision": "ok"})
        final = r.json()["respuesta"].lower()
        assert "atención médica inmediata" in final and "112" in final
    assert "DecisionSupervisor" not in llm.llamadas


@pytest.mark.parametrize("cita", ["dol", "que", "raro", "me"])
def test_cita_corta_no_cuenta(cita):
    from app.agentes.nodos import cita_en_mensaje

    assert not cita_en_mensaje(cita, "que raro, me duele el hombro con el press")


def test_cita_de_dos_palabras_y_ocho_caracteres_cuenta():
    from app.agentes.nodos import cita_en_mensaje

    assert cita_en_mensaje("algo raro", "Noto algo raro en el hombro")
    assert cita_en_mensaje("Algo RARO.", "noto algo raro en el hombro")
    assert not cita_en_mensaje("algo raro", "noto algo extraño en el hombro")


# --- N2: las exclusiones por dolor son datos de dominio (repositorio), no del hilo -----------

async def test_el_dolor_persiste_la_exclusion_antes_de_la_pausa(settings, repo, usuario):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    grafo = await _grafo(settings, repo, llm)
    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"},
                                 config_hilo(usuario))
    assert "__interrupt__" in salida
    assert await repo.exclusiones_activas(usuario) == ["press_banca"]


async def test_tras_reiniciar_el_hilo_el_programador_no_ofrece_el_ejercicio_excluido(
    settings, repo, usuario
):
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1,
                                     dias=_dias("press_banca", "sentadilla")))
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("press_banca", "sentadilla"), _plan("sentadilla", "remo_con_barra")],
    })
    saver = _saver()
    grafo = await _grafo(settings, repo, llm, saver)
    cfg = config_hilo(usuario)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"}, cfg)
    await saver.adelete_thread(str(usuario))  # reinicio del hilo (regla E): sin checkpoint
    assert not (await grafo.aget_state(cfg)).values

    salida = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "Dame una rutina nueva"}, cfg)
    assert "__interrupt__" not in salida
    assert "press_banca" in salida["ejercicios_excluidos"]
    assert "press_banca" not in _ids_rutina(await repo.rutina_actual(usuario))
    prompts = [e for nombre, e in llm.entradas if nombre == "PlanPropuesto"]
    assert prompts
    for mensajes in prompts:
        lista = mensajes[0].content.split("Usa SOLO ejercicio_id de esta lista:")[1].split("En 'fuentes'")[0]
        assert "press_banca" not in lista
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla", "remo_con_barra"}


async def test_seguridad_bloquea_el_excluido_del_repositorio_aunque_el_hilo_no_lo_tenga(
    repo, usuario
):
    from app.agentes.nodos import Nodos

    await repo.agregar_exclusion(usuario, "press_banca")
    nodos = Nodos(repo, CATALOGO, LLMFalso(), _buscador_falso)
    salida = await nodos.seguridad({
        "usuario_id": usuario, "rutina": Rutina(usuario_id=usuario, version=1,
                                                 dias=_dias("press_banca", "sentadilla")),
        "rutina_nueva": True, "lesiones": [], "ejercicios_excluidos": [],
    })
    assert salida["bloqueados"] == ["press_banca"]
    assert salida["plan_validado"] is False


async def test_get_rutina_409_tras_reiniciar_el_hilo_si_la_rutina_guardada_tiene_el_excluido(
    settings, repo, usuario
):
    # la rutina solo tiene el ejercicio con dolor: depurarla la dejaria vacia y no se guarda
    await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("press_banca")))
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [AnalisisMensaje()]})
    saver = _saver()
    grafo = await _grafo(settings, repo, llm, saver)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "pinchazo con press_banca"},
                        config_hilo(usuario))
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"press_banca"}
    await saver.adelete_thread(str(usuario))  # se pierde la pausa y la lista del checkpoint
    async with _cliente_api(grafo, repo) as c:
        r = await c.get(f"/usuarios/{usuario}/rutinas/actual")
    assert r.status_code == 409, r.text
    assert "ya no es segura" in r.json()["detail"]


# --- I-1: la urgencia por dolor en el pecho no depende solo del lexico -----------------------

SONDA_DOLOR_EXTRA = [
    "me caí de la cinta", "me sangra la rodilla", "me cedió el hombro en el press",
    "me falla la rodilla", "me falla el tobillo al saltar", "creo que me he roto el dedo",
    "me retorcí el tobillo", "me he hecho polvo la rodilla", "estoy fatal de la rodilla",
    "fatal de la espalda",
]


@pytest.mark.parametrize("texto", SONDA_DOLOR_EXTRA)
def test_sonda_extra_de_lesion_aguda_escala(texto):
    assert detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", [
    "me falla la técnica en la sentadilla", "quiero mejorar mi respiración",
    "el pecho me ha crecido", "press de pecho", "me encanta el press",
])
def test_frases_de_gimnasio_extra_no_escalan(texto):
    assert not detectar_dolor_agudo(texto)


@pytest.mark.parametrize("texto", [
    "siento presión en el pecho", "se me oprime el pecho", "me ahogo al subir escaleras",
    "no puedo respirar bien", "me arde el pecho", "me pincha el tórax",
    "noto peso en el pecho", "me falta el aire", "falta de aire al correr",
    "me cuesta respirar",
])
def test_detector_de_pecho(texto):
    from app.agentes.nodos import detectar_dolor_pecho

    assert detectar_dolor_pecho(texto)
    assert detectar_dolor_agudo(texto)  # siempre escala


async def _chat_pausa(settings, repo, usuario, mensaje, analisis):
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [analisis]})
    grafo = await _grafo(settings, repo, llm)
    async with _cliente_api(grafo, repo) as c:
        r = await c.post("/chat", json={"usuario_id": str(usuario), "mensaje": mensaje})
    assert r.status_code == 200, r.text
    assert r.json()["requiere_humano"] is True
    estado = await grafo.aget_state(config_hilo(usuario))
    return r.json()["respuesta"], estado.interrupts[0].value["motivo"]


@pytest.mark.parametrize("mensaje", [
    "siento presión en el pecho", "se me oprime el pecho", "me ahogo al subir escaleras",
    "no puedo respirar bien", "me arde el pecho",
])
async def test_pecho_por_la_api_usa_la_plantilla_de_urgencia(settings, repo, usuario, mensaje):
    respuesta, motivo = await _chat_pausa(settings, repo, usuario, mensaje, AnalisisMensaje())
    assert motivo == "dolor_pecho"
    assert "112" in respuesta and "atención médica inmediata" in respuesta


async def test_pecho_marcado_por_el_llm_con_cita_valida_usa_la_plantilla_de_urgencia(
    settings, repo, usuario
):
    mensaje = "Noto algo raro en el torso cuando corro"
    assert not detectar_dolor_agudo(mensaje)  # sin lexico: solo el LLM lo detecta
    respuesta, motivo = await _chat_pausa(settings, repo, usuario, mensaje, AnalisisMensaje(
        dolor_agudo=True, cita_dolor="algo raro en el torso", zona_dolor="pecho"))
    assert motivo == "dolor_pecho"
    assert "112" in respuesta


async def test_dolor_no_toracico_marcado_por_el_llm_sigue_siendo_dolor_agudo(
    settings, repo, usuario
):
    respuesta, motivo = await _chat_pausa(
        settings, repo, usuario, "Noto algo raro en el hombro al empujar",
        AnalisisMensaje(dolor_agudo=True, cita_dolor="algo raro en el hombro", zona_dolor="hombro"))
    assert motivo == "dolor_agudo"
    assert "112" not in respuesta


async def test_dolor_no_toracico_por_lexico_sigue_siendo_dolor_agudo(settings, repo, usuario):
    respuesta, motivo = await _chat_pausa(settings, repo, usuario, "me duele la rodilla",
                                          AnalisisMensaje())
    assert motivo == "dolor_agudo"
    assert "112" not in respuesta


async def test_pecho_gana_a_zona_sin_regla(settings, repo, usuario):
    respuesta, motivo = await _chat_pausa(
        settings, repo, usuario, "me caí y siento presión en el pecho",
        AnalisisMensaje(lesiones_nuevas=[LesionReportada(zona="otra", descripcion="costillas",
                                                         severidad="moderada")]))
    assert motivo == "dolor_pecho"
    assert "112" in respuesta


async def test_sobre_escalado_aceptado_flexiones_de_pecho_con_ardor_en_los_brazos(
    settings, repo, usuario
):
    # documentado: "pecho" + senal de dolor en el mismo mensaje se trata como urgencia aunque el
    # dolor sea en los brazos (fallo seguro aceptado por el controlador)
    _, motivo = await _chat_pausa(
        settings, repo, usuario, "hago flexiones de pecho en casa y me arden los brazos",
        AnalisisMensaje())
    assert motivo == "dolor_pecho"
