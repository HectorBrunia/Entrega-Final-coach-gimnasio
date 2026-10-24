"""docker-compose.yml y run.sh: arranque con un solo comando desde un clon limpio (sin .env)."""

import yaml

from tests.conftest import RAIZ


def _compose() -> dict:
    return yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))


def test_env_file_es_opcional():
    for nombre in ("api", "init"):
        entradas = _compose()["services"][nombre]["env_file"]
        assert all(isinstance(e, dict) and e.get("required") is False for e in entradas), nombre


def test_init_migra_e_ingiere_antes_de_la_api():
    servicios = _compose()["services"]
    comando = " ".join(servicios["init"]["command"])
    assert "alembic upgrade head" in comando and "scripts/ingerir.py" in comando
    assert servicios["init"]["image"] == servicios["api"]["image"]
    dependencias = servicios["api"]["depends_on"]
    assert dependencias["init"]["condition"] == "service_completed_successfully"
    for datos in ("postgres", "redis", "qdrant"):
        assert dependencias[datos]["condition"] == "service_healthy"
        assert "healthcheck" in servicios[datos]


def test_run_sh_no_aborta_sin_clave():
    script = (RAIZ / "run.sh").read_text(encoding="utf-8")
    assert "AVISO: GOOGLE_API_KEY o GEMINI_MODEL vacias" in script
    # sin .env se copia .env.example y se continua (no hay exit tras copiarlo)
    bloque = script.split('cp .env.example .env', 1)[1].split("else", 1)[0]
    assert "exit" not in bloque
