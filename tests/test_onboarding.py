"""Onboarding incremental y planes solo validados (fix del onboarding en varios mensajes).

Defectos reproducidos:
- RC1: un perfil repartido en varios mensajes nunca se completaba (los datos parciales se
  descartaban), asi que nunca se programaba ni se guardaba una rutina.
- RC2: con el perfil incompleto la sintesis delegaba en un LLM de texto libre que podia
  escribir un plan completo (sin catalogo, sin programador y sin filtro de seguridad).
- RC3: el aviso medico salia duplicado si el texto del LLM ya lo traia.
"""

from uuid import uuid4

import pytest

from app.agentes.estado import AnalisisMensaje, DecisionSupervisor, PerfilParcial
from app.agentes.grafo import config_hilo
from app.agentes.nodos import AVISO_MEDICO, Nodos, _con_aviso
from app.domain.modelos import Nivel, Perfil
from tests.test_grafo import (  # noqa: F401 (settings es un fixture)
    CATALOGO,
    LLMFalso,
    RepoFalso,
    _buscador_falso,
    _grafo,
    _ids_rutina,
    _plan,
    _saver,
    settings,
)

# Respuesta real (resumida) del LLM en la prueba manual: un plan en texto libre, sin ids del
# catalogo, con el aviso medico copiado del historial.
PLAN_LIBRE_EVIDENCIA = (
    "¡Perfecto! Con tu nivel intermedio y un gimnasio completo, aquí tienes tu plan de "
    "hipertrofia de 2 días, compatible con tus 3 días de CrossFit:\n\n"
    "**Día 1 - Torso**\n"
    "1. Press de banca plano con barra: 3 series x 8-10 reps\n"
    "2. Press militar con mancuernas sentado: 3 series x 10-12 reps\n"
    "3. Jalón en polea al pecho: 3 series x 10-12 reps\n"
    "4. Remo con mancuerna a una mano: 3 series x 10 reps\n\n"
    "**Día 2 - Pierna**\n"
    "1. Sentadilla con barra: 4 series x 8 reps\n"
    "2. Prensa de piernas: 3 series x 12 reps\n"
    "3. Curl femoral en máquina: 3 series x 12 reps\n\n"
    "Descansa 90 segundos entre series. Esto no es un diagnóstico médico.\n\n"
    "Esto no es un diagnóstico médico."
)

PERFIL_COMPLETO = dict(objetivo="hipertrofia", dias_disponibles=2,
                       equipo=["barra"], nivel=Nivel.intermedio)


def _turno1() -> AnalisisMensaje:
    return AnalisisMensaje(perfil=PerfilParcial(objetivo="hipertrofia", dias_disponibles=2))


def _turno2() -> AnalisisMensaje:
    return AnalisisMensaje(perfil=PerfilParcial(
        nivel=Nivel.intermedio, equipo=["barra", "mancuernas", "máquinas", "poleas"]))


def _faltan(respuesta: str) -> str:
    """Seccion de datos que faltan de la plantilla de perfil incompleto."""
    assert "Me falta" in respuesta, respuesta
    return respuesta.split("Me falta", 1)[1].split(AVISO_MEDICO)[0].lower()


# --- RC1 + regla 3: onboarding en dos mensajes ------------------------------------------------

@pytest.mark.parametrize("destino_turno2", ["programador", "sintesis"])
async def test_onboarding_en_dos_mensajes_guarda_perfil_y_programa_en_el_mismo_turno(
    settings, destino_turno2
):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [_turno1(), _turno2()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador"),
                               DecisionSupervisor(destino=destino_turno2)],
        "PlanPropuesto": [_plan("sentadilla", "press_banca")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)

    r1 = await grafo.ainvoke({"usuario_id": usuario, "mensaje": (
        "Quiero ganar masa muscular (hipertrofia). Puedo 2 días de gimnasio y además hago "
        "3 días de CrossFit.")}, cfg)
    assert usuario not in repo.perfiles
    assert "PlanPropuesto" not in llm.llamadas
    faltan = _faltan(r1["respuesta"])
    assert "nivel" in faltan and "equipo" in faltan
    assert "objetivo" not in faltan and "días disponibles" not in faltan

    r2 = await grafo.ainvoke({"usuario_id": usuario, "mensaje": (
        "Soy intermedio. Entreno en un gimnasio completo: barra, mancuernas, máquinas y "
        "poleas.")}, cfg)
    perfil = repo.perfiles[usuario]
    assert perfil.objetivo == "hipertrofia" and perfil.dias_disponibles == 2
    assert perfil.nivel == Nivel.intermedio
    assert {"barbell", "dumbbell", "machine", "cable"} <= set(perfil.equipo)
    assert usuario not in repo.borradores  # el borrador se limpia al completar el perfil
    assert "PlanPropuesto" in llm.llamadas  # el programador corre en el MISMO turno
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla", "press_banca"}
    assert r2["plan_validado"] is True
    assert r2["respuesta"].startswith("Tu rutina")
    assert "sentadilla" in r2["respuesta"]
    assert r2["respuesta"].count(AVISO_MEDICO) == 1
    assert r2["respuesta"].endswith(AVISO_MEDICO)
    assert llm.llamadas.count("texto") == 0  # ningun texto libre en todo el onboarding


async def test_borrador_de_perfil_sobrevive_a_un_reinicio_del_hilo(settings):
    usuario = uuid4()
    repo = RepoFalso()
    saver = _saver()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [_turno1(), _turno2()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm, saver)
    cfg = config_hilo(usuario)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hipertrofia, 2 dias"}, cfg)
    await saver.adelete_thread(str(usuario))  # reinicio del hilo: sin checkpoint
    assert not (await grafo.aget_state(cfg)).values

    r2 = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "intermedio, gimnasio completo"}, cfg)
    assert repo.perfiles[usuario].objetivo == "hipertrofia"
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla"}
    assert r2["respuesta"].count(AVISO_MEDICO) == 1


async def test_valores_posteriores_del_borrador_sustituyen_a_los_anteriores(settings):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [
            AnalisisMensaje(perfil=PerfilParcial(objetivo="fuerza", dias_disponibles=3)),
            AnalisisMensaje(perfil=PerfilParcial(dias_disponibles=4)),
            AnalisisMensaje(perfil=PerfilParcial(nivel=Nivel.principiante, equipo=["mancuernas"])),
        ],
        "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")],
        "PlanPropuesto": [_plan("sentadilla")],
    })
    grafo = await _grafo(settings, repo, llm)
    cfg = config_hilo(usuario)
    for mensaje in ("fuerza, 3 dias", "mejor 4 dias", "principiante con mancuernas"):
        await grafo.ainvoke({"usuario_id": usuario, "mensaje": mensaje}, cfg)
    assert repo.perfiles[usuario].dias_disponibles == 4
    assert repo.perfiles[usuario].equipo == ["dumbbell"]


async def test_equipo_vacio_tras_normalizar_cuenta_como_dato_que_falta(settings):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [AnalisisMensaje(perfil=PerfilParcial(
            objetivo="fuerza", dias_disponibles=3, nivel=Nivel.principiante,
            equipo=["cosas raras"]))],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
    })
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "fuerza 3 dias, tengo cosas raras"},
                            config_hilo(usuario))
    assert usuario not in repo.perfiles
    assert "PlanPropuesto" not in llm.llamadas
    faltan = _faltan(r["respuesta"])
    assert "equipo" in faltan
    assert "nivel" not in faltan and "objetivo" not in faltan


def test_el_prompt_del_evaluador_admite_historial_solo_para_el_perfil():
    nodos = Nodos(RepoFalso(), CATALOGO, LLMFalso(), _buscador_falso)
    sistema = nodos._prompt_evaluador({"mensaje": "hola", "mensajes": []}, None)[0].content
    assert "datos de perfil" in sistema.lower()
    assert "historial" in sistema.lower()
    # dolor y lesiones siguen limitados al ultimo mensaje
    assert "se extraen solo del ultimo mensaje" in sistema


# --- RC2: perfil incompleto -> plantilla determinista, sin LLM --------------------------------

async def test_perfil_incompleto_responde_con_plantilla_determinista_sin_llm(settings):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(
        estructuradas={"AnalisisMensaje": [AnalisisMensaje()],
                       "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")]},
        textos=[PLAN_LIBRE_EVIDENCIA],
    )
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hola, quiero entrenar"},
                            config_hilo(usuario))
    assert "texto" not in llm.llamadas
    faltan = _faltan(r["respuesta"])
    for campo in ("objetivo", "días disponibles", "equipo", "nivel"):
        assert campo in faltan
    assert "Press de banca" not in r["respuesta"]
    assert r["respuesta"].count(AVISO_MEDICO) == 1


async def test_plantilla_incluye_lo_que_ya_se_sabe(settings):
    usuario = uuid4()
    repo = RepoFalso()
    llm = LLMFalso(estructuradas={"AnalisisMensaje": [_turno1()],
                                  "DecisionSupervisor": [DecisionSupervisor(destino="sintesis")]})
    grafo = await _grafo(settings, repo, llm)
    r = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hipertrofia 2 dias"},
                            config_hilo(usuario))
    sabidos = r["respuesta"].split("Me falta")[0].lower()
    assert "hipertrofia" in sabidos and "2" in sabidos
    assert "texto" not in llm.llamadas


# --- RC2: guarda de salida de _conversar ---------------------------------------------------

def _nodos(llm, repo=None) -> Nodos:
    return Nodos(repo or RepoFalso(), CATALOGO, llm, _buscador_falso)


def _estado(usuario, perfil: bool = True, **extra) -> dict:
    estado = {"usuario_id": usuario, "mensaje": "¿y ahora qué?", **extra}
    if perfil:
        estado["perfil"] = Perfil(usuario_id=usuario, **PERFIL_COMPLETO)
    return estado


PRESCRIPCIONES = [
    PLAN_LIBRE_EVIDENCIA,
    "Haz sentadillas 4x10 y luego zancadas.",
    "Te propongo 3 series de 12 de curl de bíceps.",
    "Día 1\nTorso y brazos, sin prisa.",
    "Prueba esto:\n- Press de banca\n- Remo con barra\n- Dominadas",
    "Haz 10 repeticiones lentas de flexiones.",
]


@pytest.mark.parametrize("texto", PRESCRIPCIONES)
async def test_conversar_reemplaza_un_plan_en_texto_libre(texto):
    from app.agentes.nodos import MSG_PIDE_RUTINA

    usuario = uuid4()
    salida = await _nodos(LLMFalso(textos=[texto])).sintesis(_estado(usuario))
    assert salida["respuesta"] == f"{MSG_PIDE_RUTINA}\n\n{AVISO_MEDICO}"
    assert "dame una rutina" in MSG_PIDE_RUTINA.lower()


async def test_conversar_sin_perfil_reemplaza_el_plan_por_el_mensaje_de_perfil():
    from app.agentes.nodos import MSG_PLAN_TRAS_PERFIL

    usuario = uuid4()
    texto = await _nodos(LLMFalso(textos=[PLAN_LIBRE_EVIDENCIA]))._conversar(
        _estado(usuario, perfil=False))
    assert texto == MSG_PLAN_TRAS_PERFIL


@pytest.mark.parametrize("texto", [
    "Solo puedo ayudarte con entrenamiento.",
    "Dormir bien y comer suficiente proteína ayuda a recuperarte entre sesiones.",
    "¡Hola! ¿En qué puedo ayudarte hoy?",
    "El calentamiento previo reduce la rigidez; dedica unos minutos a movilidad.",
])
async def test_conversar_deja_pasar_respuestas_conversacionales(texto):
    usuario = uuid4()
    salida = await _nodos(LLMFalso(textos=[texto])).sintesis(_estado(usuario))
    assert salida["respuesta"] == f"{texto}\n\n{AVISO_MEDICO}"


def test_el_prompt_de_conversar_prohibe_prescribir():
    usuario = uuid4()
    llm = LLMFalso()
    nodos = _nodos(llm)
    sistema = nodos._prompt_conversar(_estado(usuario), set())[0].content.lower()
    assert "nunca prescribas" in sistema
    assert "series" in sistema and "repeticiones" in sistema and "rutinas" in sistema
    assert "dame una rutina" in sistema


# --- RC3: aviso medico una sola vez ---------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "Respuesta.",
    f"Respuesta. {AVISO_MEDICO}",
    f"Respuesta.\n\n{AVISO_MEDICO}\n\n{AVISO_MEDICO}",
    "Respuesta. esto no es un diagnostico medico",
])
def test_con_aviso_deja_un_solo_aviso_al_final(texto):
    salida = _con_aviso(texto)
    assert salida.lower().count("diagn") == 1
    assert salida == f"Respuesta.\n\n{AVISO_MEDICO}"


@pytest.mark.parametrize("veces", [1, 2])
async def test_sintesis_no_duplica_el_aviso_del_llm(veces):
    usuario = uuid4()
    texto = "Descansa bien entre sesiones." + f"\n\n{AVISO_MEDICO}" * veces
    salida = await _nodos(LLMFalso(textos=[texto])).sintesis(_estado(usuario))
    assert salida["respuesta"].count(AVISO_MEDICO) == 1
    assert salida["respuesta"].endswith(AVISO_MEDICO)


# --- persistencia real del borrador (Postgres de pruebas) ----------------------------------

@pytest.mark.integracion
async def test_borrador_en_postgres_completa_el_perfil_tras_reiniciar_el_hilo(sesion_factory, settings):
    from app.persistencia.repositorios import RepositorioDominio

    repo = RepositorioDominio(sesion_factory)
    usuario = await repo.crear_usuario()
    saver = _saver()
    llm = LLMFalso(estructuradas={
        "AnalisisMensaje": [_turno1(), _turno2()],
        "DecisionSupervisor": [DecisionSupervisor(destino="programador")],
        "PlanPropuesto": [_plan("sentadilla", "press_banca")],
    })
    grafo = await _grafo(settings, repo, llm, saver)
    cfg = config_hilo(usuario)
    await grafo.ainvoke({"usuario_id": usuario, "mensaje": "hipertrofia, 2 dias"}, cfg)
    assert await repo.obtener_perfil(usuario) is None
    borrador = await repo.obtener_perfil_borrador(usuario)
    assert borrador is not None and borrador.objetivo == "hipertrofia"

    await saver.adelete_thread(str(usuario))
    r2 = await grafo.ainvoke({"usuario_id": usuario, "mensaje": "intermedio, gimnasio completo"}, cfg)
    perfil = await repo.obtener_perfil(usuario)
    assert perfil is not None and perfil.dias_disponibles == 2 and perfil.nivel == Nivel.intermedio
    assert await repo.obtener_perfil_borrador(usuario) is None
    assert _ids_rutina(await repo.rutina_actual(usuario)) == {"sentadilla", "press_banca"}
    assert r2["respuesta"].count(AVISO_MEDICO) == 1
