"""Arranque sin GOOGLE_API_KEY: la API funciona salvo el coach conversacional (503 claro)."""

from contextlib import asynccontextmanager
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.memory import InMemorySaver

from app.agentes.estado import AnalisisMensaje
from app.demo.dobles import RepositorioMemoria
from app.llm import MSG_NO_CONFIGURADO, NO_CONFIGURADO, LLMNoDisponible, LLMSinConfigurar, crear_llm
from app.main import Constructores, crear_app
from app.settings import Settings
from tests.conftest import RAIZ

MENSAJE = (
    "Falta configurar GOOGLE_API_KEY (y GEMINI_MODEL) en .env para usar el coach conversacional"
)


def _cfg(**extra) -> Settings:
    valores = dict(google_api_key="", gemini_model="",
                   catalogo_path=RAIZ / "data/catalogo/exercises.json", guias_dir=RAIZ / "data/guias")
    return Settings(_env_file=None, **{**valores, **extra})


def test_mensaje_exacto():
    assert MSG_NO_CONFIGURADO == MENSAJE


def test_crear_llm_sin_clave_devuelve_un_modelo_que_responde_no_configurado():
    llm = crear_llm(_cfg())
    assert isinstance(llm, LLMSinConfigurar)
    with pytest.raises(LLMNoDisponible) as exc:
        llm.with_structured_output(AnalisisMensaje).invoke("hola")
    assert exc.value.motivo == NO_CONFIGURADO
    assert exc.value.mensaje_publico == MENSAJE


@pytest.mark.parametrize("clave,modelo", [("", "gemini-x"), ("k", "")])
def test_falta_clave_o_modelo_no_construye_gemini(clave, modelo):
    assert isinstance(crear_llm(_cfg(google_api_key=clave, gemini_model=modelo)), LLMSinConfigurar)


async def _ok():
    return None


@asynccontextmanager
async def _checkpointer_memoria(_url):
    yield InMemorySaver()


@pytest.mark.asyncio
async def test_api_sin_clave_arranca_y_solo_el_chat_responde_503():
    repo = RepositorioMemoria()
    app = crear_app(
        _cfg(), repo=repo, comprobaciones={"postgres": _ok, "redis": _ok, "qdrant": _ok},
        constructores=Constructores(checkpointer=_checkpointer_memoria),
    )
    async with app.router.lifespan_context(app):
        assert app.state.grafo is not None  # el grafo se construye igual (perfil y rutinas)
        transporte = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transporte, base_url="http://t") as c:
            salud = await c.get("/health")
            docs = await c.get("/docs")
            usuario = await c.post("/usuarios", json={})
            uid = usuario.json()["id"]
            chat = await c.post("/chat", json={"usuario_id": uid, "mensaje": "hola"})
            hitl = await c.post(f"/hitl/{uid}/reanudar", json={"revision": "ok"})
            perfil = await c.get(f"/usuarios/{uid}/perfil")
            rutina = await c.get(f"/usuarios/{uid}/rutinas/actual")
            entreno = await c.post(f"/usuarios/{uid}/entrenos", json={
                "fecha": str(date(2026, 10, 1)), "ejercicio_id": "Barbell_Squat", "series": 3,
                "repeticiones": 8, "peso_kg": 60, "rpe": 7})

    assert salud.status_code == 200
    assert salud.json() == {"status": "ok", "llm": "no_configurado",
                            "servicios": {"postgres": "ok", "redis": "ok", "qdrant": "ok"}}
    assert docs.status_code == 200
    assert usuario.status_code == 201
    assert chat.status_code == 503 and chat.json() == {"detail": MENSAJE}
    assert hitl.status_code == 503 and hitl.json() == {"detail": MENSAJE}
    assert perfil.status_code == 404
    assert rutina.status_code == 404
    assert entreno.status_code == 201


@pytest.mark.asyncio
async def test_health_informa_llm_configurado_sin_cambiar_el_codigo():
    async def _falla():
        raise RuntimeError("caido")

    app = crear_app(
        _cfg(google_api_key="k", gemini_model="m"), repo=RepositorioMemoria(),
        comprobaciones={"postgres": _ok, "redis": _falla, "qdrant": _ok},
        constructores=Constructores(checkpointer=_checkpointer_memoria),
    )
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            salud = await c.get("/health")
    assert salud.status_code == 503
    assert salud.json()["llm"] == "configurado"


def test_importar_la_app_no_carga_torch_ni_sentence_transformers():
    """Los modelos de ML se importan de forma perezosa (solo al codificar)."""
    import subprocess
    import sys

    codigo = (
        "import sys, app.main; "
        "print(sorted(m for m in ('torch', 'sentence_transformers', 'transformers') "
        "if m in sys.modules))"
    )
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "[]"
