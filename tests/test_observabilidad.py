import logging

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import app.observabilidad as obs
from app.observabilidad import configurar_trazas, contexto_traza
from tests.test_api import _cfg


@pytest.fixture(autouse=True)
def _estado_limpio():
    """Cada prueba parte sin trazas configuradas y deja el proceso como lo encontro."""
    LangChainInstrumentor().uninstrument()
    obs._reiniciar_para_pruebas()
    yield
    LangChainInstrumentor().uninstrument()
    obs._reiniciar_para_pruebas()


def test_configurar_trazas_es_idempotente():
    s = _cfg()
    configurar_trazas(s)
    configurar_trazas(s)  # no debe lanzar ni duplicar instrumentación
    assert LangChainInstrumentor().is_instrumented_by_opentelemetry


def test_configurar_trazas_registra_proveedor_una_sola_vez(monkeypatch):
    llamadas = []
    monkeypatch.setattr(obs, "_registrar_proveedor", lambda s: llamadas.append(s) or TracerProvider())
    configurar_trazas(_cfg())
    configurar_trazas(_cfg())
    assert len(llamadas) == 1


def test_llamada_langchain_instrumentada_produce_spans():
    exportador = InMemorySpanExporter()
    proveedor = TracerProvider()
    proveedor.add_span_processor(SimpleSpanProcessor(exportador))
    LangChainInstrumentor().instrument(tracer_provider=proveedor, skip_dep_check=True)

    FakeListChatModel(responses=["hola"]).invoke("di hola")

    assert len(exportador.get_finished_spans()) >= 1


def test_fallo_de_configuracion_no_lanza_ni_filtra_secretos(monkeypatch, caplog):
    def falla(_s):
        raise RuntimeError("fallo con http://usuario:secreto@host")

    monkeypatch.setattr(obs, "_registrar_proveedor", falla)
    with caplog.at_level(logging.WARNING):
        configurar_trazas(_cfg())  # no debe lanzar
    assert "secreto" not in caplog.text
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_contexto_traza_anade_thread_id_y_usuario_id():
    exportador = InMemorySpanExporter()
    proveedor = TracerProvider()
    proveedor.add_span_processor(SimpleSpanProcessor(exportador))
    monkey_tracer = proveedor.get_tracer("t")
    obs_tracer_original = obs._tracer
    obs._tracer = lambda: monkey_tracer
    try:
        with contexto_traza("chat", thread_id="t-1", usuario_id="u-1"):
            assert trace.get_current_span().is_recording()
    finally:
        obs._tracer = obs_tracer_original

    (span,) = exportador.get_finished_spans()
    assert span.name == "chat"
    assert span.attributes["thread_id"] == "t-1"
    assert span.attributes["usuario_id"] == "u-1"


# --- Cableado en el lifespan ---------------------------------------------------

from app.main import Constructores, crear_app  # noqa: E402
from tests.test_api import GrafoFalso, RepoFalso, _catalogo  # noqa: E402


async def test_lifespan_configura_trazas_antes_de_construir_el_grafo():
    orden = []

    async def grafo(*a, **k):
        orden.append("grafo")
        return GrafoFalso()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def checkpointer(_u):
        yield object()

    app = crear_app(
        _cfg(), repo=RepoFalso(), catalogo=_catalogo(),
        constructores=Constructores(
            motor=lambda _u: None, checkpointer=checkpointer, grafo=grafo,
            trazas=lambda _s: orden.append("trazas"),
        ),
    )
    async with app.router.lifespan_context(app):
        pass
    assert orden == ["trazas", "grafo"]


async def test_lifespan_sigue_sin_degradar_si_las_trazas_fallan():
    def trazas(_s):
        raise RuntimeError("boom")

    grafo = GrafoFalso()
    app = crear_app(
        _cfg(), grafo=grafo, repo=RepoFalso(), catalogo=_catalogo(),
        constructores=Constructores(trazas=trazas),
    )
    async with app.router.lifespan_context(app):
        assert app.state.grafo is grafo


def test_endpoint_trazas_anade_ruta_otlp_solo_si_falta():
    assert obs._endpoint_trazas("http://localhost:6006") == "http://localhost:6006/v1/traces"
    assert obs._endpoint_trazas("http://localhost:6006/") == "http://localhost:6006/v1/traces"
    assert obs._endpoint_trazas("http://h:6006/v1/traces") == "http://h:6006/v1/traces"
