"""requirements.txt / requirements-dev.txt no se desalinean de pyproject.toml."""

import re
import tomllib

from tests.conftest import RAIZ

# Pines que solo estan en requirements.txt: torch se fija aparte para instalar su build CPU.
SOLO_EN_REQUIREMENTS = {"torch"}


def _pyproject() -> dict:
    return tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))


def _lineas(nombre: str) -> list[str]:
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def _pines(lineas: list[str]) -> dict[str, str]:
    pines = {}
    for linea in lineas:
        if linea.startswith("-"):
            continue
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+)(\[[^\]]+\])?==([^\s;]+)", linea)
        assert m, f"requisito sin version exacta: {linea!r}"
        pines[m.group(1).lower() + (m.group(2) or "")] = m.group(3)
    return pines


def test_requirements_fija_exactamente_las_dependencias_de_pyproject():
    esperado = _pines(_pyproject()["project"]["dependencies"])
    actual = _pines(_lineas("requirements.txt"))
    extra = {k: v for k, v in actual.items() if k in SOLO_EN_REQUIREMENTS}
    assert {k: v for k, v in actual.items() if k not in SOLO_EN_REQUIREMENTS} == esperado
    assert set(extra) == SOLO_EN_REQUIREMENTS


def test_torch_se_instala_desde_el_indice_cpu():
    lineas = _lineas("requirements.txt")
    assert "--extra-index-url https://download.pytorch.org/whl/cpu" in lineas
    assert re.fullmatch(r"\d+\.\d+\.\d+", _pines(lineas)["torch"])  # sin sufijo +cpu


def test_requirements_dev_incluye_runtime_y_dependencias_de_pruebas():
    lineas = _lineas("requirements-dev.txt")
    assert "-r requirements.txt" in lineas
    assert _pines(lineas) == _pines(_pyproject()["project"]["optional-dependencies"]["dev"])


def test_el_dockerfile_instala_desde_requirements():
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    assert "pip install -r requirements.txt" in dockerfile
