from pathlib import Path

from app.catalogo.cargador import cargar_catalogo

FIXTURE = Path(__file__).parent / "fixtures" / "catalogo_muestra.json"


def test_carga_tres_ejercicios_normalizados():
    ejercicios = cargar_catalogo(FIXTURE)
    assert len(ejercicios) == 3
    assert all(e.nivel in {"principiante", "intermedio", "avanzado"} for e in ejercicios)


def test_equipo_nulo_se_normaliza_a_cuerpo():
    ejercicios = cargar_catalogo(FIXTURE)
    assert any(e.equipo == "cuerpo" for e in ejercicios)
