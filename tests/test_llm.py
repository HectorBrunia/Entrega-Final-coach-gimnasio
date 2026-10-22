import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import GoogleInvalidRequestError, GoogleRateLimitError

from app.llm import LLMNoDisponible, crear_llm
from app.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        qdrant_collection="c",
        google_api_key="clave-falsa",
        gemini_model="modelo-de-prueba",
        gemini_rpm=600,
        phoenix_collector_endpoint="http://localhost:6006",
        embedding_model="modelo-falso",
    )


def _parchear_generacion(monkeypatch, fallos: int, error: Exception) -> list[int]:
    """Sustituye la llamada real a Gemini: falla `fallos` veces y luego responde."""
    llamadas: list[int] = []

    async def _falso(self, messages, stop=None, run_manager=None, **kwargs):
        llamadas.append(1)
        if len(llamadas) <= fallos:
            raise error
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="ok"))])

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", _falso)
    return llamadas


def test_crear_llm_usa_settings(settings):
    llm = crear_llm(settings)
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model.endswith("modelo-de-prueba")
    assert llm.google_api_key.get_secret_value() == "clave-falsa"
    assert llm.rate_limiter is not None
    # los reintentos del SDK quedan desactivados: solo reintenta nuestra politica ante 429
    assert llm.max_retries == 1


async def test_reintenta_ante_429_y_luego_responde(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 2, GoogleRateLimitError("429 RESOURCE_EXHAUSTED"))
    llm = crear_llm(settings, reintentos=3, espera_base=0.0)
    respuesta = await llm.ainvoke("hola")
    assert respuesta.content == "ok"
    assert len(llamadas) == 3


async def test_agota_reintentos_y_lanza_llm_no_disponible(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 99, GoogleRateLimitError("429 RESOURCE_EXHAUSTED"))
    llm = crear_llm(settings, reintentos=2, espera_base=0.0)
    with pytest.raises(LLMNoDisponible):
        await llm.ainvoke("hola")
    assert len(llamadas) == 3  # intento inicial + 2 reintentos


async def test_no_reintenta_errores_que_no_son_429(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 99, GoogleInvalidRequestError("400 INVALID_ARGUMENT"))
    llm = crear_llm(settings, reintentos=3, espera_base=0.0)
    with pytest.raises(GoogleInvalidRequestError):
        await llm.ainvoke("hola")
    assert len(llamadas) == 1
