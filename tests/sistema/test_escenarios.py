"""Pruebas de sistema (spec sec. 10): stack real de docker compose y Gemini real.

Ejecutar: `pytest tests/sistema -m sistema -v` (ver tests/sistema/conftest.py).
Las aserciones son estructurales (rutina guardada, banderas, estado del grafo, aviso medico)
para no depender de la redaccion del LLM. Cada escenario deja una traza `sistema.<escenario>`
en Phoenix y la prueba comprueba que llego.
"""

import re
from datetime import date, timedelta
from uuid import UUID

import pytest

from app.agentes.grafo import config_hilo
from app.agentes.nodos import AVISO_MEDICO
from app.domain.modelos import DiaRutina, EjercicioPlanificado, Lesion, Rutina
from app.rag.ingesta import PREFIJO_FUENTE_GUIA, documentos_desde_guias
from app.safety.reglas import filtrar_por_lesiones
from tests.sistema.conftest import (
    comprobar_traza_en_phoenix,
    crear_usuario,
    registrar_perfil,
    traza_escenario,
)

pytestmark = pytest.mark.sistema

HOMBRO_DERECHO = Lesion(zona="hombro_derecho", severidad="moderada", activa=True)
PRESS_HOMBRO = "Barbell_Shoulder_Press"
PRESS_BANCA = "Barbell_Bench_Press_-_Medium_Grip"


# --- utilidades ---------------------------------------------------------------------------

async def _chat(cliente, usuario_id: str, mensaje: str) -> dict:
    r = await cliente.post("/chat", json={"usuario_id": usuario_id, "mensaje": mensaje})
    assert r.status_code == 200, r.text
    return r.json()


async def _rutina(cliente, usuario_id: str) -> dict | None:
    r = await cliente.get(f"/usuarios/{usuario_id}/rutinas/actual")
    if r.status_code == 404:
        return None
    assert r.status_code == 200, r.text
    return r.json()


def _ids(rutina: dict) -> list[str]:
    return [e["ejercicio_id"] for d in rutina["dias"] for e in d["ejercicios"]]


def _bloqueados(ids: list[str], catalogo, lesiones: list[Lesion]) -> list[str]:
    return [i for i, _ in filtrar_por_lesiones([catalogo[i] for i in ids], lesiones).bloqueados]


def _plan(*dias: list[str]) -> list[DiaRutina]:
    return [
        DiaRutina(nombre=f"Día {n}", ejercicios=[
            EjercicioPlanificado(ejercicio_id=i, series=3, repeticiones="8-10",
                                 descanso_seg=90, fuentes=["catalogo"])
            for i in ids
        ])
        for n, ids in enumerate(dias, 1)
    ]


def _prescripciones(rutina: dict) -> dict[str, list[tuple]]:
    """ejercicio_id -> prescripciones (series, repeticiones, descanso) en toda la rutina."""
    res: dict[str, list[tuple]] = {}
    for d in rutina["dias"]:
        for e in d["ejercicios"]:
            res.setdefault(e["ejercicio_id"], []).append(
                (e["series"], e["repeticiones"], e["descanso_seg"]))
    return {k: sorted(v) for k, v in res.items()}


def _normalizar(texto: str) -> str:
    """Minusculas y separadores unificados: 'Barbell_Squat' y 'Barbell Squat' -> 'barbell squat'."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto.lower()).split())


def _ejercicios_mencionados(texto: str, catalogo) -> set[str]:
    norm = f" {_normalizar(texto)} "
    return {
        e.id for e in catalogo.values()
        if any(f" {f} " in norm for f in {_normalizar(e.id), _normalizar(e.nombre)} if f)
    }


async def _con_rutina(repo, usuario_id: str, *dias: list[str]) -> None:
    await repo.guardar_rutina(Rutina(usuario_id=UUID(usuario_id), version=1, dias=_plan(*dias)))


# --- 1. Onboarding completo -------------------------------------------------------------------

async def test_onboarding_completo_extrae_perfil_y_respeta_dias(cliente, catalogo, entorno_sistema):
    usuario_id = await crear_usuario(cliente)
    async with traza_escenario("onboarding_completo") as trace_id:
        r = await _chat(cliente, usuario_id, (
            "Hola, soy nuevo. Mi objetivo es ganar fuerza, puedo entrenar 3 días por semana, "
            "entreno en un gimnasio con barra, mancuernas y máquinas, y mi nivel es principiante. "
            "¿Me armas una rutina?"
        ))
        if await _rutina(cliente, usuario_id) is None:
            # el coach puede confirmar el perfil antes de programar: se le pide el plan
            r = await _chat(cliente, usuario_id, "Sí, genera ya mi rutina de 3 días con esos datos.")

    perfil = (await cliente.get(f"/usuarios/{usuario_id}/perfil")).json()
    assert perfil["dias_disponibles"] == 3
    assert perfil["nivel"] == "principiante"

    rutina = await _rutina(cliente, usuario_id)
    assert rutina is not None, f"no se guardo ninguna rutina; respuesta: {r['respuesta'][:300]}"
    assert len(rutina["dias"]) == 3  # respeta los dias disponibles
    assert all(d["ejercicios"] for d in rutina["dias"])
    assert set(_ids(rutina)) <= catalogo.keys()  # nada inventado fuera del catalogo
    assert r["requiere_humano"] is False
    assert AVISO_MEDICO in r["respuesta"]
    await comprobar_traza_en_phoenix(entorno_sistema, "onboarding_completo", trace_id)


# --- 2. Ajuste semanal --------------------------------------------------------------------------

async def test_ajuste_semanal_usa_historial_y_cita_guia(cliente, repo, catalogo, entorno_sistema):
    usuario_id = await crear_usuario(cliente)
    await registrar_perfil(repo, usuario_id)
    dias = (["Barbell_Squat", "Dumbbell_Bicep_Curl"],
            [PRESS_BANCA, "Leg_Press"],
            ["Barbell_Deadlift", "Hammer_Curls"])
    await _con_rutina(repo, usuario_id, *dias)
    original = await _rutina(cliente, usuario_id)

    lunes = date.today() - timedelta(days=date.today().weekday() + 7)
    for n, ids in enumerate(dias):
        for i in ids:
            r = await cliente.post(f"/usuarios/{usuario_id}/entrenos", json={
                "fecha": (lunes + timedelta(days=2 * n)).isoformat(), "ejercicio_id": i,
                "series": 3, "repeticiones": 10, "peso_kg": 40, "rpe": 6,
                "notas": "todas las series en el tope del rango, sobraban repeticiones",
            })
            assert r.status_code == 201, r.text

    async with traza_escenario("ajuste_semanal") as trace_id:
        r = await _chat(cliente, usuario_id, (
            "Ya registré mis entrenos de la semana: completé todas las series en el tope del rango "
            "con RPE 6. Ajusta la progresión de mi rutina según mi historial."
        ))

    rutina = await _rutina(cliente, usuario_id)
    assert rutina["version"] > original["version"]  # se guardo una version ajustada
    assert set(_ids(rutina)) <= catalogo.keys()
    # el ajuste cambio la prescripcion de algun ejercicio registrado (o lo sustituyo)
    antes, despues = _prescripciones(original), _prescripciones(rutina)
    registrados = {i for ids in dias for i in ids}
    assert any(despues.get(i) != antes[i] for i in registrados), "la rutina ajustada no cambia nada"

    guias = documentos_desde_guias(entorno_sistema.guias_dir)
    citables = {d.id for d in guias} | {d.fuente for d in guias}
    fuentes = {f for d in rutina["dias"] for e in d["ejercicios"] for f in e["fuentes"]}
    # campo estructurado `fuentes` de la rutina guardada (no el texto de la respuesta)
    citadas = {f for f in fuentes if f in citables or f.startswith(PREFIJO_FUENTE_GUIA)}
    assert citadas, f"la rutina ajustada no cita ninguna guia; fuentes={sorted(fuentes)}"
    assert r["requiere_humano"] is False
    assert AVISO_MEDICO in r["respuesta"]
    await comprobar_traza_en_phoenix(entorno_sistema, "ajuste_semanal", trace_id)


# --- 3. Lesion activa ----------------------------------------------------------------------------

async def test_lesion_activa_no_muestra_press_militar(cliente, catalogo, usuario_con_hombro_lesionado, entorno_sistema):
    usuario_id = usuario_con_hombro_lesionado
    async with traza_escenario("lesion_activa") as trace_id:
        r = await _chat(cliente, usuario_id, "Dame una rutina de hombro para 3 días")

    assert r["requiere_humano"] is False
    rutina = await _rutina(cliente, usuario_id)
    assert rutina is not None, f"no se guardo ninguna rutina; respuesta: {r['respuesta'][:300]}"
    ids = _ids(rutina)
    assert ids and set(ids) <= catalogo.keys()
    # la rutina guardada pasa el filtro determinista: ningun ejercicio bloqueado por la lesion
    assert _bloqueados(ids, catalogo, [HOMBRO_DERECHO]) == []
    assert PRESS_HOMBRO not in ids
    assert AVISO_MEDICO in r["respuesta"]
    await comprobar_traza_en_phoenix(entorno_sistema, "lesion_activa", trace_id)


async def test_lesion_nueva_retira_ejercicios_bloqueados_de_la_rutina(cliente, repo, catalogo, entorno_sistema):
    usuario_id = await crear_usuario(cliente)
    await registrar_perfil(repo, usuario_id)
    await _con_rutina(repo, usuario_id, [PRESS_HOMBRO, "Leg_Press"], [PRESS_BANCA, "Leg_Extensions"])
    assert _bloqueados(_ids(await _rutina(cliente, usuario_id)), catalogo, [HOMBRO_DERECHO])

    async with traza_escenario("lesion_nueva") as trace_id:
        r = await _chat(cliente, usuario_id,
                        "Ayer me lesioné el hombro derecho, es una lesión moderada.")

    assert [l.zona for l in await repo.lesiones_activas(UUID(usuario_id))] == ["hombro_derecho"]
    rutina = await _rutina(cliente, usuario_id)
    ids = _ids(rutina)
    assert rutina["version"] > 1
    assert _bloqueados(ids, catalogo, [HOMBRO_DERECHO]) == []
    assert PRESS_HOMBRO not in ids and PRESS_BANCA not in ids
    assert {"Leg_Press", "Leg_Extensions"} <= set(ids)  # solo se retira lo bloqueado
    assert r["requiere_humano"] is False
    assert AVISO_MEDICO in r["respuesta"]
    await comprobar_traza_en_phoenix(entorno_sistema, "lesion_nueva", trace_id)


# --- 4. Dolor agudo ----------------------------------------------------------------------------

async def test_dolor_agudo_pausa_y_no_vuelve_a_recomendar_el_ejercicio(
    cliente, repo, app_sistema, catalogo, entorno_sistema
):
    usuario_id = await crear_usuario(cliente)
    await registrar_perfil(repo, usuario_id)
    await _con_rutina(repo, usuario_id, [PRESS_BANCA, "Dumbbell_Bicep_Curl"], ["Leg_Press", "Hammer_Curls"])
    nombre = catalogo[PRESS_BANCA].nombre
    config = config_hilo(UUID(usuario_id))

    async with traza_escenario("dolor_agudo") as trace_id:
        pausa = await _chat(cliente, usuario_id,
                            f"Tengo un dolor agudo en el hombro cuando hago {nombre}, empeora en cada repetición.")
        # el grafo queda en pausa HITL y el ejercicio ya salio de la rutina guardada
        assert pausa["requiere_humano"] is True
        # texto de plantilla de la app (no del LLM): pausa HITL
        assert "profesional" in pausa["respuesta"].lower()
        assert AVISO_MEDICO in pausa["respuesta"]
        estado = await app_sistema.state.grafo.aget_state(config)
        assert estado.next == ("hitl",)
        assert PRESS_BANCA in estado.values["ejercicios_excluidos"]
        # durante la pausa la API no sirve la rutina (409 "rutina en revision"); la version
        # guardada se comprueba en el repositorio
        en_pausa = await cliente.get(f"/usuarios/{usuario_id}/rutinas/actual")
        assert en_pausa.status_code == 409, en_pausa.text
        guardada = await repo.rutina_actual(UUID(usuario_id))
        assert guardada is not None
        assert PRESS_BANCA not in {p.ejercicio_id for d in guardada.dias for p in d.ejercicios}

        r = await cliente.post(f"/hitl/{usuario_id}/reanudar",
                               json={"revision": "Revisado por fisioterapeuta: seguir sin ese ejercicio."})
        assert r.status_code == 200, r.text
        reanudada = r.json()
        assert reanudada["requiere_humano"] is False
        assert "profesional" in reanudada["respuesta"].lower()  # plantilla del nodo hitl
        assert AVISO_MEDICO in reanudada["respuesta"]
        assert not (await app_sistema.state.grafo.aget_state(config)).next

        nueva = await _chat(cliente, usuario_id, "Dame una rutina nueva de 3 días para esta semana.")

    rutina = await _rutina(cliente, usuario_id)
    ids = _ids(rutina)
    # v1 inicial, v2 sin el ejercicio (retirado al pausar), v3 la rutina nueva pedida despues
    assert rutina["version"] >= 3, f"no se genero rutina nueva; respuesta: {nueva['respuesta'][:300]}"
    assert PRESS_BANCA not in ids  # no se vuelve a recomendar
    assert AVISO_MEDICO in nueva["respuesta"]
    assert (await cliente.post(f"/hitl/{usuario_id}/reanudar", json={"revision": "x"})).status_code == 409
    await comprobar_traza_en_phoenix(entorno_sistema, "dolor_agudo", trace_id)


# --- 5. Pregunta fuera de alcance ---------------------------------------------------------------

async def test_pregunta_fuera_de_alcance_rechaza_sin_inventar_plan(cliente, repo, catalogo, entorno_sistema):
    usuario_id = await crear_usuario(cliente)
    await registrar_perfil(repo, usuario_id)
    antes = await _rutina(cliente, usuario_id)
    async with traza_escenario("fuera_de_alcance") as trace_id:
        r = await _chat(cliente, usuario_id,
                        "¿En qué criptomoneda debería invertir mis ahorros este mes para duplicarlos?")

    assert r["requiere_humano"] is False
    # (a) el turno no crea ninguna version de rutina (404 antes y despues cuenta como igual)
    assert await _rutina(cliente, usuario_id) == antes
    # (b) no recomienda ningun ejercicio del catalogo (ni por id ni por nombre)
    mencionados = _ejercicios_mencionados(r["respuesta"], catalogo)
    assert not mencionados, f"la respuesta menciona ejercicios: {sorted(mencionados)[:5]}"
    assert r["respuesta"].strip()
    # (c) sin aviso medico: no se exige porque la app lo anade a toda respuesta de sintesis
    #     (ver task-11-report.md, ronda de correcciones 1); no hay senal estructural de rechazo.
    await comprobar_traza_en_phoenix(entorno_sistema, "fuera_de_alcance", trace_id)
