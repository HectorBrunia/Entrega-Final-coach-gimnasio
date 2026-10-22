"""I4: el equipo del perfil se normaliza al vocabulario del catalogo (sin red ni servicios)."""

import logging
from pathlib import Path
from uuid import uuid4

import pytest

from app.agentes.nodos import Nodos
from app.catalogo.cargador import cargar_catalogo
from app.domain.equipo import EQUIPO_CATALOGO, SINONIMOS_EQUIPO, normalizar_equipo
from app.domain.modelos import Nivel, Perfil

CATALOGO_REAL = Path(__file__).resolve().parent.parent / "data" / "catalogo" / "exercises.json"


@pytest.fixture(scope="module")
def ejercicios():
    return cargar_catalogo(CATALOGO_REAL)


def _perfil(equipo: list[str]) -> Perfil:
    return Perfil(usuario_id=uuid4(), objetivo="fuerza", dias_disponibles=3, equipo=equipo,
                  nivel=Nivel.principiante)


def test_vocabulario_canonico_es_el_del_catalogo_cargado(ejercicios):
    assert {e.equipo for e in ejercicios} == EQUIPO_CATALOGO


def test_todos_los_sinonimos_apuntan_al_vocabulario_del_catalogo():
    assert all(set(v) <= EQUIPO_CATALOGO for v in SINONIMOS_EQUIPO.values())


@pytest.mark.parametrize("entrada, esperado", [
    (["barra"], ["barbell"]),
    (["Mancuernas"], ["dumbbell"]),
    (["máquinas", "poleas"], ["machine", "cable"]),
    (["pesas rusas", "bandas elásticas"], ["kettlebells", "bands"]),
    (["peso corporal"], ["cuerpo"]),
    (["barra Z"], ["e-z curl bar"]),
    (["barra", "barbell", "Barra"], ["barbell"]),  # sin duplicados
    (["dumbbell", "cuerpo"], ["dumbbell", "cuerpo"]),  # lo canonico se conserva
])
def test_sinonimos_en_espanol_se_mapean(entrada, esperado):
    assert normalizar_equipo(entrada) == esperado
    assert _perfil(entrada).equipo == esperado


def test_equipo_desconocido_se_registra_y_se_ignora(caplog):
    with caplog.at_level(logging.WARNING, logger="app.domain.equipo"):
        perfil = _perfil(["mancuernas", "trineo de arrastre"])
    assert perfil.equipo == ["dumbbell"]
    assert "trineo de arrastre" in caplog.text


def test_filtro_por_equipo_reduce_el_catalogo_con_solo_mancuernas(ejercicios):
    perfil = _perfil(["mancuernas"])
    candidatos = Nodos._candidatos(perfil, ejercicios, set(), [])
    assert candidatos  # hay candidatos
    assert {e.equipo for e in candidatos} <= {"dumbbell", "cuerpo"}
    # antes del arreglo "mancuernas" no coincidia con nada y se devolvia el catalogo entero
    todos = Nodos._candidatos(_perfil([]), ejercicios, set(), [])
    assert {e.equipo for e in todos} - {"dumbbell", "cuerpo"}


def test_filtro_por_equipo_deja_fuera_kettlebells_y_poleas(ejercicios):
    candidatos = Nodos._candidatos(_perfil(["barra", "mancuernas"]), ejercicios, set(), [])
    equipos = {e.equipo for e in candidatos}
    assert "kettlebells" not in equipos and "cable" not in equipos
