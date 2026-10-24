"""Ronda 1 de revision del fix de onboarding (I1-I3 y menores M1, M3, M4)."""

from uuid import uuid4

import pytest

from app.agentes.estado import AnalisisMensaje, DecisionSupervisor, PerfilParcial
from app.agentes.grafo import config_hilo
from app.agentes.nodos import AVISO_MEDICO, Nodos, _con_aviso, parece_prescripcion
from app.domain.modelos import Nivel, Perfil, PerfilBorrador, Rutina
from tests.test_grafo import (  # noqa: F401 (settings es un fixture)
    CATALOGO,
    LLMFalso,
    RepoFalso,
    _buscador_falso,
    _dias,
    _grafo,
    _ids_rutina,
    _plan,
    settings,
)
from tests.test_onboarding import PERFIL_COMPLETO, _estado, _nodos

# --- I1(a): la expresion regular sola detecta los formatos de la revision -----------------

FALLOS_DE_LA_REVISION = [
    "Haz 3 sets de 12 de sentadilla.",
    "3 sets x 12",
    "Lunes: sentadilla, press banca y remo.\nMiércoles: peso muerto y dominadas.",
    "Día A: sentadilla y press.\nDía B: peso muerto y remo.",
    "Sesión A: sentadilla, press de banca.",
    "Semana 1: sentadilla 3 series, press 3 series",
    "El primer día haz sentadilla y press de banca.",
    "Haz sentadillas con 60 kg.",
    "peso muerto rumano con 40 kg dos veces por semana",
    "Sentadilla: 4 series, 10 cada una",
    "Sentadilla x10, press x8",
    "haz 8-10 repes",
    "4 rondas de 10 sentadillas y 10 flexiones",
    "4 vueltas de 10 burpees",
    "plancha 3 veces 45 segundos",
    "- Sentadilla\n- Press de banca",
    "✅ Sentadilla búlgara\n✅ Hip thrust",
    "🏋️ Sentadilla\n💪 Curl de bíceps",
    "**Lunes**\nSentadilla\nPress de banca",
    "1. Búlgaras 2. Goblet 3. Romanian",
    "| Ejercicio | Series | Repes |\n|---|---|---|\n| Sentadilla | 3 | 10 |",
    "Haz sentadilla, press de banca, remo, dominadas y curl cada lunes y jueves.",
]

# Falsos positivos aceptados (fallo seguro): se sustituyen aunque no sean un plan.
FALSOS_POSITIVOS_ACEPTADOS = [
    "El RIR indica cuántas repeticiones te quedan en reserva.",
    "- El press de banca trabaja pecho\n- La sentadilla trabaja piernas\n- El remo trabaja espalda",
    "1920x1080",
]

BENIGNOS = [
    "Solo puedo ayudarte con entrenamiento.",
    "Dormir bien y comer suficiente proteína ayuda a recuperarte entre sesiones.",
    "¡Hola! ¿En qué puedo ayudarte hoy?",
    "El calentamiento previo reduce la rigidez; dedica unos minutos a movilidad.",
    "Lo estás haciendo bien desde el día 1.",
    "En tu sesión 2 descansaste poco.",
    "Entrenar 2x por semana cada grupo muscular es razonable.",
    "Descansa entre series lo que necesites.",
]


@pytest.mark.parametrize("texto", FALLOS_DE_LA_REVISION)
def test_la_expresion_regular_detecta_los_formatos_de_plan_de_la_revision(texto):
    assert parece_prescripcion(texto)


@pytest.mark.parametrize("texto", FALSOS_POSITIVOS_ACEPTADOS)
def test_falsos_positivos_documentados_y_aceptados(texto):
    assert parece_prescripcion(texto)


@pytest.mark.parametrize("texto", BENIGNOS)
def test_textos_benignos_no_parecen_prescripcion(texto):
    assert not parece_prescripcion(texto)


# --- I1(b): segunda red independiente, salida estructurada del LLM ---------------------------

async def test_plan_que_la_regex_no_ve_pero_el_llm_marca_se_sustituye():
    from app.agentes.estado import RespuestaConversacion
    from app.agentes.nodos import MSG_PIDE_RUTINA

    texto = "Empieza con el movimiento de bisagra que te comenté y súmale el empuje vertical."
    assert not parece_prescripcion(texto)
    llm = LLMFalso(estructuradas={"RespuestaConversacion": [
        RespuestaConversacion(texto=texto, contiene_ejercicios=True)]})
    salida = await _nodos(llm).sintesis(_estado(uuid4()))
    assert salida["respuesta"] == f"{MSG_PIDE_RUTINA}\n\n{AVISO_MEDICO}"


@pytest.mark.parametrize("texto", BENIGNOS)
async def test_respuesta_benigna_sin_marca_ni_regex_pasa(texto):
    from app.agentes.estado import RespuestaConversacion

    llm = LLMFalso(estructuradas={"RespuestaConversacion": [
        RespuestaConversacion(texto=texto, contiene_ejercicios=False)]})
    salida = await _nodos(llm).sintesis(_estado(uuid4()))
    assert salida["respuesta"] == f"{texto}\n\n{AVISO_MEDICO}"


@pytest.mark.parametrize("fallo", [RuntimeError("429"), None])
async def test_si_falla_la_salida_estructurada_se_responde_el_mensaje_fijo(fallo):
    from app.agentes.nodos import MSG_PIDE_RUTINA

    # excepcion o salida vacia (None): falla cerrado con el mensaje fijo
    llm = LLMFalso(estructuradas={"RespuestaConversacion": [fallo]})
    salida = await _nodos(llm).sintesis(_estado(uuid4()))
    assert salida["respuesta"] == f"{MSG_PIDE_RUTINA}\n\n{AVISO_MEDICO}"


def test_el_prompt_de_conversar_define_contiene_ejercicios():
    sistema = _nodos(LLMFalso())._prompt_conversar(_estado(uuid4()), set())[0].content
    assert "contiene_ejercicios" in sistema


# --- I2: la respuesta con la rutina no lleva texto del LLM -----------------------------------

CENTINELA = "CENTINELA_DEL_LLM: añade también 3x15 de sentadilla búlgara con 20 kg"


@pytest.mark.parametrize("destino", ["programador", "progreso"])
async def test_la_rutina_formateada_no_contiene_texto_del_llm(settings, destino):
    from app.agentes.estado import PlanPropuesto

    usuario = uuid4()
    repo = RepoFalso()
    repo.perfiles[usuario] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    if destino == "progreso":
        await repo.guardar_rutina(Rutina(usuario_id=usuario, version=1, dias=_dias("sentadilla")))
    dias = _dias("sentadilla", "press_banca")
    dias[0].ejercicios[0].fuentes = ["guia_hipertrofia#volumen", CENTINELA]
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino=destino)],
        "PlanPropuesto": [PlanPropuesto(dias=dias, explicacion=CENTINELA)],
    })
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "dame una rutina"}, config_hilo(usuario))
    assert r["plan_validado"] is True
    assert "CENTINELA" not in r["respuesta"]
    assert "guia_hipertrofia#volumen" in r["respuesta"]  # la fuente con forma de id se muestra
    assert "hipertrofia" in r["respuesta"] and "intermedio" in r["respuesta"]
    if destino == "progreso":
        assert "entrenos registrados" in r["respuesta"]


def test_el_prompt_del_programador_no_pide_explicacion_libre():
    usuario = uuid4()
    perfil = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    sistema = _nodos(LLMFalso())._prompt_programador(
        {"usuario_id": usuario, "mensaje": "rutina"}, perfil, list(CATALOGO.values()), [], [], ""
    )[0].content
    assert "explicacion" not in sistema


# --- I3: los datos del historial solo rellenan lo que falta ----------------------------------

@pytest.mark.parametrize("almacenado", ["borrador", "perfil"])
@pytest.mark.parametrize("actual, esperado", [
    (None, Nivel.intermedio), (Nivel.avanzado, Nivel.avanzado)])
async def test_el_historial_no_sobrescribe_el_nivel_guardado(settings, almacenado, actual, esperado):
    usuario = uuid4()
    repo = RepoFalso()
    if almacenado == "perfil":
        repo.perfiles[usuario] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    else:
        repo.borradores[usuario] = PerfilBorrador(objetivo="hipertrofia", nivel=Nivel.intermedio)
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(
            perfil=PerfilParcial(nivel=actual) if actual else None,
            perfil_historial=PerfilParcial(nivel=Nivel.principiante, dias_disponibles=3))],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    grafo = await _grafo(settings, repo, llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "vale"}, config_hilo(usuario))
    if almacenado == "perfil":
        assert repo.perfiles[usuario].nivel == esperado
        assert repo.perfiles[usuario].dias_disponibles == 2  # el historial no pisa lo guardado
    else:
        assert repo.borradores[usuario].nivel == esperado
        assert repo.borradores[usuario].dias_disponibles == 3  # el historial rellena lo que falta


def test_el_prompt_del_evaluador_muestra_el_borrador_y_separa_historial():
    nodos = Nodos(RepoFalso(), CATALOGO, LLMFalso(), _buscador_falso)
    sistema = nodos._prompt_evaluador({"mensaje": "hola", "mensajes": []}, None,
                                      borrador=PerfilBorrador(objetivo="fuerza"))[0].content
    assert "perfil_historial" in sistema and "fuerza" in sistema


async def test_perfil_sin_cambios_no_se_reescribe(settings):
    usuario = uuid4()
    repo = RepoFalso()
    repo.perfiles[usuario] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    guardados = []
    original = repo.guardar_perfil

    async def contar(perfil):
        guardados.append(perfil)
        await original(perfil)

    repo.guardar_perfil = contar
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(perfil=PerfilParcial(nivel=Nivel.intermedio))],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
    })
    grafo = await _grafo(settings, repo, llm)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "soy intermedio"}, config_hilo(usuario))
    assert guardados == []


# --- M1: regla 3 tambien si el supervisor elige seguridad sin rutina -------------------------

async def test_perfil_completado_con_supervisor_en_seguridad_programa(settings):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(perfil=PerfilParcial(**PERFIL_COMPLETO))],
        "DecisionSupervisor": [DecisionSupervisor(destino="seguridad")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "todo mi perfil"}, config_hilo(usuario))
    assert "PlanPropuesto" in llm.llamadas
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
    assert r["respuesta"].startswith("Tu rutina")


# --- M3: aviso tolerante a espacios y sin restos de puntuacion -------------------------------

@pytest.mark.parametrize("texto, esperado", [
    ("Hola.\n\nesto  no es un\ndiagnóstico médico.", "Hola."),
    ("Esto no es un diagnóstico médico. Hola.", "Hola."),
    ("Hola. ¡Esto no es un diagnóstico médico!", "Hola."),
    ("Hola (esto no es un diagnóstico médico).", "Hola."),
    ("Hola, esto no es un diagnóstico médico, consulta a un profesional.",
     "Hola, consulta a un profesional."),
])
def test_con_aviso_tolerante_y_sin_restos(texto, esperado):
    assert _con_aviso(texto) == f"{esperado}\n\n{AVISO_MEDICO}"
