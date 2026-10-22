"""Reglas de seguridad contra el catalogo real de free-exercise-db (sin red ni servicios)."""

from pathlib import Path

import pytest

from app.catalogo.cargador import cargar_catalogo
from app.domain.modelos import Ejercicio, Lesion, Nivel
from app.safety import reglas as reglas_mod
from app.safety.reglas import (
    REGLAS_LESION,
    ReglaZona,
    ReglasInvalidas,
    ejercicio_bloqueado,
    filtrar_por_lesiones,
    validar_reglas_contra_catalogo,
)

CATALOGO_REAL = Path(__file__).resolve().parent.parent / "data" / "catalogo" / "exercises.json"


@pytest.fixture(scope="module")
def catalogo() -> dict[str, Ejercicio]:
    return {e.id: e for e in cargar_catalogo(CATALOGO_REAL)}


def _lesion(zona: str) -> Lesion:
    return Lesion(zona=zona, severidad="moderada", activa=True)


def _ej(id_: str, nombre: str, musculo: str, secundarios: list[str] | None = None) -> Ejercicio:
    return Ejercicio(id=id_, nombre=nombre, musculo_primario=musculo,
                     musculos_secundarios=secundarios or [], equipo="cuerpo",
                     nivel=Nivel.principiante, instrucciones=[])


def test_catalogo_real_tiene_876_ejercicios(catalogo):
    assert len(catalogo) == 876


def test_validar_reglas_no_lanza_con_catalogo_real(catalogo):
    validar_reglas_contra_catalogo(catalogo)


@pytest.mark.parametrize("zona", sorted(REGLAS_LESION))
def test_cada_zona_bloquea_al_menos_un_ejercicio_real(catalogo, zona):
    res = filtrar_por_lesiones(list(catalogo.values()), [_lesion(zona)])
    assert res.bloqueados


@pytest.mark.parametrize(("zona", "ejercicio_id"), [
    ("hombro_derecho", "Barbell_Shoulder_Press"),
    ("hombro_izquierdo", "Barbell_Shoulder_Press"),
    ("rodilla_izquierda", "Barbell_Squat"),
    ("rodilla_derecha", "Barbell_Squat"),
    ("zona_lumbar", "Barbell_Deadlift"),
])
def test_ejercicio_de_riesgo_queda_bloqueado(catalogo, zona, ejercicio_id):
    res = filtrar_por_lesiones(list(catalogo.values()), [_lesion(zona)])
    assert (ejercicio_id, zona) in res.bloqueados
    assert ejercicio_id not in {e.id for e in res.permitidos}


@pytest.mark.parametrize("zona", sorted(REGLAS_LESION))
def test_ningun_bloqueado_aparece_en_permitidos(catalogo, zona):
    res = filtrar_por_lesiones(list(catalogo.values()), [_lesion(zona)])
    bloqueados = {i for i, _ in res.bloqueados}
    permitidos = {e.id for e in res.permitidos}
    assert not bloqueados & permitidos
    assert bloqueados | permitidos == set(catalogo)
    regla = REGLAS_LESION[zona]
    assert bloqueados == {e.id for e in catalogo.values() if ejercicio_bloqueado(e, regla)}


def test_todas_las_zonas_a_la_vez_no_dejan_pasar_bloqueados(catalogo):
    res = filtrar_por_lesiones(list(catalogo.values()), [_lesion(z) for z in REGLAS_LESION])
    assert not {i for i, _ in res.bloqueados} & {e.id for e in res.permitidos}


def test_patron_ignora_mayusculas_y_separadores():
    regla = ReglaZona(musculos=frozenset(), patrones_nombre=("upright row",), ids_extra=frozenset())
    for id_, nombre in [("Upright_Row", "x"), ("x", "Upright-Row"), ("x", "UPRIGHT  ROW"),
                        ("Cable_Upright_Rows", "y")]:
        assert ejercicio_bloqueado(_ej(id_, nombre, "biceps"), regla)
    assert not ejercicio_bloqueado(_ej("Bicep_Curl", "Bicep Curl", "biceps"), regla)


def test_musculo_secundario_bloquea():
    regla = ReglaZona(musculos=frozenset({"shoulders"}), patrones_nombre=(), ids_extra=frozenset())
    assert ejercicio_bloqueado(_ej("a", "a", "chest", ["shoulders"]), regla)
    assert ejercicio_bloqueado(_ej("a", "a", "Shoulders"), regla)
    assert not ejercicio_bloqueado(_ej("a", "a", "chest", ["triceps"]), regla)


def test_id_extra_bloquea():
    regla = ReglaZona(musculos=frozenset(), patrones_nombre=(), ids_extra=frozenset({"a"}))
    assert ejercicio_bloqueado(_ej("a", "a", "chest"), regla)
    assert not ejercicio_bloqueado(_ej("b", "b", "chest"), regla)


def _catalogo_pequeno() -> dict[str, Ejercicio]:
    ejs = [_ej("Front_Raise", "Front Raise", "shoulders"), _ej("Bicep_Curl", "Bicep Curl", "biceps")]
    return {e.id: e for e in ejs}


def test_validar_lanza_si_un_id_extra_no_existe(monkeypatch):
    regla = ReglaZona(musculos=frozenset({"shoulders"}), patrones_nombre=(),
                      ids_extra=frozenset({"Ejercicio_Fantasma"}))
    monkeypatch.setattr(reglas_mod, "REGLAS_LESION", {"hombro_derecho": regla})
    with pytest.raises(ReglasInvalidas, match="hombro_derecho.*Ejercicio_Fantasma"):
        validar_reglas_contra_catalogo(_catalogo_pequeno())


def test_validar_lanza_si_una_zona_no_bloquea_nada(monkeypatch):
    regla = ReglaZona(musculos=frozenset({"quadriceps"}), patrones_nombre=("squat",),
                      ids_extra=frozenset())
    monkeypatch.setattr(reglas_mod, "REGLAS_LESION", {"rodilla_derecha": regla})
    with pytest.raises(ReglasInvalidas, match="rodilla_derecha"):
        validar_reglas_contra_catalogo(_catalogo_pequeno())


def test_validar_lanza_si_un_musculo_no_existe_en_el_catalogo(monkeypatch):
    # Una errata en un musculo ("shoulder") dejaria pasar ejercicios en silencio.
    regla = ReglaZona(musculos=frozenset({"shoulder"}), patrones_nombre=("raise",),
                      ids_extra=frozenset())
    monkeypatch.setattr(reglas_mod, "REGLAS_LESION", {"hombro_derecho": regla})
    with pytest.raises(ReglasInvalidas, match="hombro_derecho.*shoulder"):
        validar_reglas_contra_catalogo(_catalogo_pequeno())


def test_validar_con_catalogo_pequeno_valido_no_lanza(monkeypatch):
    regla = ReglaZona(musculos=frozenset({"shoulders"}), patrones_nombre=(),
                      ids_extra=frozenset({"Bicep_Curl"}))
    monkeypatch.setattr(reglas_mod, "REGLAS_LESION", {"hombro_derecho": regla})
    validar_reglas_contra_catalogo(_catalogo_pequeno())


def test_regla_es_inmutable():
    regla = next(iter(REGLAS_LESION.values()))
    with pytest.raises(Exception):
        regla.musculos = frozenset()  # type: ignore[misc]


@pytest.mark.parametrize("ejercicio_id", [
    # Presses con kettlebell: empiezan con una cargada desde el suelo (revision Task 4b).
    "Alternating_Kettlebell_Press",
    "Kettlebell_Arnold_Press",
    "Kettlebell_Seesaw_Press",
    "One-Arm_Kettlebell_Para_Press",
    "Kettlebell_Seated_Press",
    # Presses por encima de la cabeza hallados en el reescaneo de falsos negativos.
    "Seated_Dumbbell_Press",
    "Arnold_Dumbbell_Press",
    "Bradford_Rocky_Presses",
    "Cuban_Press",
    "Anti-Gravity_Press",
    "Dumbbell_One-Arm_Triceps_Extension",
    "Seated_Triceps_Press",
    "See-Saw_Press_Alternating_Side_Press",
])
def test_presses_de_riesgo_lumbar_quedan_bloqueados(catalogo, ejercicio_id):
    res = filtrar_por_lesiones(list(catalogo.values()), [_lesion("zona_lumbar")])
    assert (ejercicio_id, "zona_lumbar") in res.bloqueados
    assert ejercicio_id not in {e.id for e in res.permitidos}
