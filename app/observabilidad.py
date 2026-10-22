"""Trazas con Phoenix: OpenTelemetry + instrumentacion OpenInference de LangChain/LangGraph."""

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse

from opentelemetry import trace

from app.settings import Settings

logger = logging.getLogger(__name__)

_NOMBRE_TRACER = "coach-gimnasio"
_bloqueo = threading.Lock()
_configurado = False


def _tracer() -> trace.Tracer:
    return trace.get_tracer(_NOMBRE_TRACER)


def _endpoint_trazas(base: str) -> str:
    """El exportador HTTP usa la URL tal cual: si solo llega el host, se anade la ruta OTLP."""
    if urlparse(base).path.strip("/"):
        return base
    return base.rstrip("/") + "/v1/traces"


def _registrar_proveedor(settings: Settings):
    from phoenix.otel import register

    return register(
        endpoint=_endpoint_trazas(settings.phoenix_collector_endpoint),
        protocol="http/protobuf",
        project_name="coach-gimnasio",
        batch=True,
        auto_instrument=False,
        verbose=False,
    )


def _reiniciar_para_pruebas() -> None:
    global _configurado
    _configurado = False


def configurar_trazas(settings: Settings) -> None:
    """Registra el TracerProvider hacia Phoenix e instrumenta LangChain. Idempotente.

    Nunca lanza: si algo falla se avisa (sin datos sensibles) y la app sigue sin trazas.
    """
    global _configurado
    with _bloqueo:
        if _configurado:
            return
        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor

            proveedor = _registrar_proveedor(settings)
            LangChainInstrumentor().instrument(tracer_provider=proveedor)
            _configurado = True
        except Exception as exc:
            logger.warning("No se pudieron configurar las trazas: %s", type(exc).__name__)


@contextmanager
def contexto_traza(nombre: str, *, thread_id: str, usuario_id: str) -> Iterator[None]:
    """Span con `thread_id` y `usuario_id`; los spans del grafo cuelgan de el."""
    from openinference.instrumentation import using_attributes

    atributos = {"thread_id": str(thread_id), "usuario_id": str(usuario_id)}
    with (
        _tracer().start_as_current_span(nombre, attributes=atributos),
        using_attributes(session_id=atributos["thread_id"], user_id=atributos["usuario_id"]),
    ):
        yield
