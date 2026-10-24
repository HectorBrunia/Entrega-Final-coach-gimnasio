"""Ronda 2 de revision: regex ampliada y campos estrictos de la rutina validada."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.agentes.estado import AnalisisMensaje, DecisionSupervisor, PlanPropuesto
from app.agentes.grafo import config_hilo
from app.agentes.nodos import AVISO_MEDICO, MSG_FALLO_PLAN, parece_prescripcion
from app.domain.modelos import (
    DiaRutina, EjercicioPlanificado, Perfil, Rutina, nombre_dia_valido, repeticiones_validas,
)
from tests.test_grafo import (  # noqa: F401 (settings es un fixture)
    LLMFalso,
    RepoFalso,
    _grafo,
    _plan,
    settings,
)
from tests.test_onboarding import PERFIL_COMPLETO, _nodos

# --- 1. formatos que la sonda de la re-revision no detectaba ---------------------------------

FALLOS_DE_LA_SONDA = [
    "Haz cuatro tandas de diez sentadillas.",
    "En sentadilla, 5 de 5 con buena técnica.",
    "Press de banca 3 por 12.",
    "A) Press militar 4/8",
    "Deja el press militar a 8-10 y el curl a 12-15.",
    "Tres tandas de dominadas al fallo.",
    "Todo a 3 tandas.",
    "Upper: press de banca y remo. Lower: sentadilla y peso muerto.",
    "Empuje: press militar; Tirón: dominadas; Pierna: sentadilla.",
    "Torso: press y remo. Pierna: sentadilla.",
    "Primera sesión: sentadilla y press. Segunda sesión: peso muerto y remo.",
    "Sube a 62,5 en el press.",
    "40 segundos y descansa 20, ocho veces: burpees.",
    "30 s on / 30 s off de burpees",
    "Un Tabata de burpees al final.",
    "50 flexiones al día.",
    "20 burpees seguidos cada mañana.",
    "10 minutos de cinta y luego 15 de remo.",
    "Te sugiero sentadilla y peso muerto.",
    "Te dejo una idea: hip thrust y zancadas.",
    "Mañana: sentadilla y press.",
    "Para glúteo: hip thrust y patada en polea.",
    "Te recomiendo el hip thrust.",
    "Haz press banca hoy.",
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
    "El RIR es cuánto te queda en el depósito antes del fallo; úsalo para regular el esfuerzo.",
    "Calienta unos minutos antes de entrenar y sube el pulso poco a poco.",
    "¡Ánimo! La constancia es lo que más cuenta.",
    "Las agujetas suelen durar entre 24 y 72 horas; es normal al empezar.",
    "Para perder grasa necesitas un déficit calórico moderado.",
    "La sobrecarga progresiva consiste en aumentar poco a poco el estímulo.",
    "La creatina es uno de los suplementos más estudiados; consulta a un profesional si dudas.",
    "Si quieres un plan, escribe 'dame una rutina'.",
    "Dormir 7-9 horas ayuda a recuperarte.",
    "Bebe agua a lo largo del día.",
]


@pytest.mark.parametrize("texto", FALLOS_DE_LA_SONDA)
def test_la_regex_detecta_los_fallos_de_la_sonda(texto):
    assert parece_prescripcion(texto)


@pytest.mark.parametrize("texto", BENIGNOS)
def test_respuestas_benignas_sin_falsos_positivos(texto):
    assert not parece_prescripcion(texto)


# --- 2. campos estrictos de la rutina ---------------------------------------------------------

@pytest.mark.parametrize("valor", ["8", "10", "8-10", "12-15"])
def test_repeticiones_validas(valor):
    assert repeticiones_validas(valor)


@pytest.mark.parametrize("valor", ["8-10 y añade press militar 5x5", "al fallo", "AMRAP", "30 s",
                                   "100", "8 a 10", "8-10\n- press militar", ""])
def test_repeticiones_invalidas(valor):
    assert not repeticiones_validas(valor)


@pytest.mark.parametrize("nombre", ["Día 1", "Dia A", "Día 1 - Torso", "Día 2: Pierna",
                                    "Upper", "Empuje (pecho y hombro)"])
def test_nombres_de_dia_validos(nombre):
    assert nombre_dia_valido(nombre)


@pytest.mark.parametrize("nombre", [
    "Día 1: además haz press militar 5x5",
    "Día 1\n- press militar",
    "- Día 1",
    "1. Torso",
    "Torso con 60 kg",
    "Pierna 4 series",
    "Un nombre de día larguísimo que pasa de cuarenta caracteres",
    "",
])
def test_nombres_de_dia_invalidos(nombre):
    assert not nombre_dia_valido(nombre)


def _dia(nombre="Día 1", repeticiones="8-10") -> dict:
    return {"nombre": nombre, "ejercicios": [{
        "ejercicio_id": "sentadilla", "series": 3, "repeticiones": repeticiones,
        "descanso_seg": 90, "fuentes": ["catalogo"]}]}


@pytest.mark.parametrize("dia", [_dia(nombre="Día 1: además haz press militar 5x5"),
                                 _dia(repeticiones="8-10 y luego 5x5 de press militar")])
def test_la_propuesta_del_llm_con_campos_invalidos_no_valida(dia):
    with pytest.raises(ValidationError):
        PlanPropuesto.model_validate({"dias": [dia]})


def test_la_propuesta_valida_sigue_validando():
    plan = PlanPropuesto.model_validate({"dias": [_dia()]})
    assert plan.dias[0].ejercicios[0].repeticiones == "8-10"


async def test_nombre_de_dia_malicioso_nunca_llega_al_usuario(settings):
    usuario = uuid4()
    repo = RepoFalso()
    repo.perfiles[usuario] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    try:
        PlanPropuesto.model_validate({"dias": [_dia(nombre="Día 1: además haz press militar 5x5")]})
    except ValidationError as exc:
        error = exc  # lo que lanzaria el parser de la salida estructurada
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [error],
    })
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "dame una rutina"}, config_hilo(usuario))
    assert "press militar" not in r["respuesta"].lower()
    assert r["respuesta"] == f"{MSG_FALLO_PLAN}\n\n{AVISO_MEDICO}"
    assert await repo.rutina_actual(usuario) is None


async def test_rutina_guardada_con_campos_invalidos_se_muestra_saneada():
    # defensa en profundidad: una rutina ya guardada (p. ej. anterior a esta validacion)
    usuario = uuid4()
    malo = EjercicioPlanificado.model_construct(
        ejercicio_id="sentadilla", series=3, repeticiones="8-10 y añade press militar 5x5",
        descanso_seg=90, fuentes=[])
    dia = DiaRutina.model_construct(nombre="Día 1: además haz press militar 5x5", ejercicios=[malo])
    rutina = Rutina.model_construct(usuario_id=usuario, version=1, dias=[dia])
    salida = await _nodos(LLMFalso()).sintesis({
        "usuario_id": usuario, "mensaje": "mi rutina", "rutina": rutina, "plan_validado": True,
        "perfil": Perfil(usuario_id=usuario, **PERFIL_COMPLETO)})
    assert "press militar" not in salida["respuesta"].lower()
    assert "Día 1" in salida["respuesta"]
    assert "sentadilla" in salida["respuesta"]


def test_el_prompt_del_programador_explica_el_formato():
    usuario = uuid4()
    perfil = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    from tests.test_grafo import CATALOGO

    sistema = _nodos(LLMFalso())._prompt_programador(
        {"usuario_id": usuario, "mensaje": "rutina"}, perfil, list(CATALOGO.values()), [], [], ""
    )[0].content
    assert "8-10" in sistema and "40" in sistema


def test_plan_de_pruebas_con_dias_del_dominio_sigue_valido():
    assert isinstance(_plan("sentadilla"), PlanPropuesto)


# --- 3. fuentes de la rutina normalizadas a guias reales -------------------------------------

def _guias():
    from pathlib import Path

    from app.rag.ingesta import fuentes_de_guias

    return fuentes_de_guias(Path(__file__).resolve().parent.parent / "data" / "guias")


def test_fuentes_de_guias_salen_de_los_archivos_cargados():
    assert _guias() == frozenset({"guia:progresion", "guia:tecnica_basica",
                                  "guia:consideraciones_por_zona_lesion"})


def test_caso_del_sistema_normaliza_los_nombres_de_archivo():
    from app.agentes.nodos import normalizar_fuentes

    assert normalizar_fuentes(["progresion", "tecnica_basica"], _guias()) == [
        "guia:progresion", "guia:tecnica_basica"]


@pytest.mark.parametrize("fuentes, esperado", [
    (["guia:progresion"], ["guia:progresion"]),
    (["progresion#sobrecarga-progresiva"], ["guia:progresion"]),
    (["guia progresion", "Guía: tecnica_basica"], ["guia:progresion", "guia:tecnica_basica"]),
    (["progresion", "guia:progresion", "progresion#x"], ["guia:progresion"]),
    (["guia_hipertrofia_inventada", "catalogo", "ACSM 2009", ""], []),
])
def test_normalizar_fuentes(fuentes, esperado):
    from app.agentes.nodos import normalizar_fuentes

    assert normalizar_fuentes(fuentes, _guias()) == esperado


async def test_la_rutina_guardada_y_mostrada_solo_cita_guias_reales(settings):
    from app.domain.modelos import EjercicioPlanificado as EP

    usuario = uuid4()
    repo = RepoFalso()
    repo.perfiles[usuario] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    plan = PlanPropuesto(dias=[DiaRutina(nombre="Día 1", ejercicios=[
        EP(ejercicio_id="sentadilla", series=3, repeticiones="8-10", descanso_seg=90,
           fuentes=["progresion", "tecnica_basica#calentamiento", "guia_inventada"])])])
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [plan],
    })
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "dame una rutina"}, config_hilo(usuario))
    guardada = await repo.rutina_actual(usuario)
    assert guardada.dias[0].ejercicios[0].fuentes == ["guia:progresion", "guia:tecnica_basica"]
    assert "Fuentes: guia:progresion, guia:tecnica_basica" in r["respuesta"]
    assert "inventada" not in r["respuesta"]


def test_el_prompt_del_programador_lista_las_fuentes_canonicas():
    from app.agentes.nodos import Nodos
    from tests.test_grafo import CATALOGO, _buscador_falso

    usuario = uuid4()
    nodos = Nodos(RepoFalso(), CATALOGO, LLMFalso(), _buscador_falso, fuentes_guia=_guias())
    sistema = nodos._prompt_programador(
        {"usuario_id": usuario, "mensaje": "rutina"}, Perfil(usuario_id=usuario, **PERFIL_COMPLETO),
        list(CATALOGO.values()), [], [], "")[0].content
    assert "guia:progresion" in sistema and "guia:tecnica_basica" in sistema
