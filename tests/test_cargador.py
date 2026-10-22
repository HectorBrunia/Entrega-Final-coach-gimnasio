import json
from pathlib import Path

import pytest

from app.catalogo.cargador import CatalogoInvalido, cargar_catalogo
from app.domain.modelos import Nivel

FIXTURE = Path(__file__).parent / "fixtures" / "catalogo_muestra.json"


def test_carga_tres_ejercicios_normalizados():
    ejercicios = cargar_catalogo(FIXTURE)
    assert len(ejercicios) == 3
    assert all(e.nivel in {"principiante", "intermedio", "avanzado"} for e in ejercicios)


def test_equipo_nulo_se_normaliza_a_cuerpo():
    ejercicios = cargar_catalogo(FIXTURE)
    assert any(e.equipo == "cuerpo" for e in ejercicios)


def test_cada_registro_se_mapea_correctamente():
    por_id = {e.id: e for e in cargar_catalogo(FIXTURE)}
    esperado = {
        "Barbell_Squat": ("Barbell Squat", "quadriceps", "barbell", Nivel.intermedio),
        "Push_Up": ("Push Up", "chest", "cuerpo", Nivel.principiante),
        "Muscle_Up": ("Muscle Up", "lats", "cuerpo", Nivel.avanzado),
    }
    assert set(por_id) == set(esperado)
    for id_, (nombre, musculo, equipo, nivel) in esperado.items():
        e = por_id[id_]
        assert e.nombre == nombre
        assert e.musculo_primario == musculo
        assert e.equipo == equipo
        assert e.nivel == nivel


def _escribir(tmp_path, registro):
    ruta = tmp_path / "malo.json"
    ruta.write_text(json.dumps([registro]), encoding="utf-8")
    return ruta


def _registro(**cambios):
    base = {
        "id": "Roto_1",
        "name": "Roto",
        "primaryMuscles": ["chest"],
        "secondaryMuscles": [],
        "equipment": "barbell",
        "level": "beginner",
        "instructions": ["x"],
    }
    return base | cambios


def test_nivel_desconocido_lanza_catalogo_invalido_con_id(tmp_path):
    ruta = _escribir(tmp_path, _registro(level="legendario"))
    with pytest.raises(CatalogoInvalido, match="Roto_1"):
        cargar_catalogo(ruta)


def test_musculo_primario_vacio_lanza_catalogo_invalido_con_id(tmp_path):
    ruta = _escribir(tmp_path, _registro(primaryMuscles=[]))
    with pytest.raises(CatalogoInvalido, match="Roto_1"):
        cargar_catalogo(ruta)
