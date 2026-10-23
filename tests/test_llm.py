import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import (
    GoogleAPIError,
    GoogleAuthenticationError,
    GoogleInvalidRequestError,
    GoogleRateLimitError,
)

from app.llm import MSG_CONFIGURACION, MSG_TRANSITORIO, LLMNoDisponible, crear_llm
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
    # los reintentos del SDK quedan desactivados: solo reintenta nuestra politica
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


def _error_503() -> GoogleAPIError:
    """Instancia real, como la que langchain_google_genai produce desde un ServerError 503."""
    cuerpo = {"error": {"code": 503, "message": "This model is currently experiencing high demand",
                        "status": "UNAVAILABLE"}}
    return GoogleAPIError(code=503, response_json=cuerpo, response=None)


async def test_reintenta_ante_503_y_luego_responde(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 2, _error_503())
    llm = crear_llm(settings, reintentos=3, espera_base=0.0)
    respuesta = await llm.ainvoke("hola")
    assert respuesta.content == "ok"
    assert len(llamadas) == 3


@pytest.mark.parametrize("codigo", [500, 502, 503, 504])
async def test_reintenta_cualquier_5xx(settings, monkeypatch, codigo):
    error = GoogleAPIError(code=codigo, response_json={"error": {"code": codigo}}, response=None)
    llamadas = _parchear_generacion(monkeypatch, 1, error)
    llm = crear_llm(settings, reintentos=2, espera_base=0.0)
    assert (await llm.ainvoke("hola")).content == "ok"
    assert len(llamadas) == 2


async def test_503_persistente_lanza_llm_no_disponible_transitorio(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 99, _error_503())
    llm = crear_llm(settings, reintentos=2, espera_base=0.0)
    with pytest.raises(LLMNoDisponible) as info:
        await llm.ainvoke("hola")
    assert len(llamadas) == 3
    assert info.value.mensaje_publico == MSG_TRANSITORIO
    assert "high demand" not in str(info.value)


@pytest.mark.parametrize("error", [
    GoogleAuthenticationError("401 UNAUTHENTICATED api key not valid: clave-secreta"),
    GoogleInvalidRequestError("400 INVALID_ARGUMENT"),
])
async def test_error_permanente_no_se_reintenta(settings, monkeypatch, error):
    llamadas = _parchear_generacion(monkeypatch, 99, error)
    llm = crear_llm(settings, reintentos=3, espera_base=0.0)
    with pytest.raises(LLMNoDisponible) as info:
        await llm.ainvoke("hola")
    assert len(llamadas) == 1
    assert info.value.mensaje_publico == MSG_CONFIGURACION
    assert "clave-secreta" not in str(info.value)


async def test_error_ajeno_se_propaga_sin_reintentar(settings, monkeypatch):
    llamadas = _parchear_generacion(monkeypatch, 99, ValueError("validacion"))
    llm = crear_llm(settings, reintentos=3, espera_base=0.0)
    with pytest.raises(ValueError):
        await llm.ainvoke("hola")
    assert len(llamadas) == 1


def test_crear_llm_toma_reintentos_de_settings(settings):
    settings.llm_reintentos, settings.llm_espera_base, settings.llm_espera_max = 5, 0.5, 7.0
    llm = crear_llm(settings)
    assert (llm.reintentos_429, llm.espera_base_429, llm.espera_max_429) == (5, 0.5, 7.0)
    assert llm._espera(10) == 7.0


def test_reintenta_en_modo_sincrono(settings, monkeypatch):
    llamadas: list[int] = []

    def _falso(self, messages, stop=None, run_manager=None, **kwargs):
        llamadas.append(1)
        if len(llamadas) <= 1:
            raise _error_503()
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="ok"))])

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_generate", _falso)
    llm = crear_llm(settings, reintentos=2, espera_base=0.0)
    assert llm.invoke("hola").content == "ok"
    assert len(llamadas) == 2
