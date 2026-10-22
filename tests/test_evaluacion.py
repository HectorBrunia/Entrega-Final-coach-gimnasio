"""Golden set y parte determinista de evaluacion/evaluar.py (sin LLM ni servicios)."""

import json

import pytest

from app.catalogo.cargador import cargar_catalogo
from evaluacion.evaluar import GOLDEN, evaluar_seguridad_determinista
from tests.conftest import RAIZ


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def catalogo_real():
    return {e.id: e for e in cargar_catalogo(RAIZ / "data/catalogo/exercises.json")}


def test_golden_set_tiene_al_menos_10_casos_bien_formados(golden):
    casos = golden["casos"]
    assert len(casos) >= 10
    assert len({c["id"] for c in casos}) == len(casos)
    for c in casos:
        assert c["consulta"].strip()
        if c["tipo"] == "recuperacion":
            assert c["esperados"]
        else:
            assert c["tipo"] == "seguridad" and c["zona"] and c["prohibidos"]


def test_filtro_bloquea_todos_los_prohibidos_del_golden_set(golden, catalogo_real):
    seguridad = [c for c in golden["casos"] if c["tipo"] == "seguridad"]
    res = evaluar_seguridad_determinista(seguridad, catalogo_real)
    assert res["resumen"] == {"casos": len(seguridad), "violaciones": 0, "sobrebloqueos": 0,
                              "ids_fuera_del_catalogo": 0}


def test_la_evaluacion_detecta_una_violacion(catalogo_real):
    caso = {"id": "X", "tipo": "seguridad", "zona": "hombro_derecho", "consulta": "x",
            "prohibidos": ["Barbell_Shoulder_Press", "Dumbbell_Bicep_Curl", "No_Existe"],
            "permitidos": ["Side_Lateral_Raise"]}
    res = evaluar_seguridad_determinista([caso], catalogo_real)["casos"][0]
    assert res["violaciones"] == ["Dumbbell_Bicep_Curl", "No_Existe"]
    assert res["sobrebloqueos"] == ["Side_Lateral_Raise"]
    assert res["ids_fuera_del_catalogo"] == ["No_Existe"]
    assert not res["ok"]
