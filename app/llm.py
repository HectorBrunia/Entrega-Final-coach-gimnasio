"""Fabrica del LLM (Gemini) con limite de tasa y reintentos ante errores transitorios."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
from google.genai.errors import ClientError, ServerError
from langchain_core.exceptions import (
    ModelAuthenticationError,
    ModelInvalidRequestError,
    ModelNotFoundError,
    ModelPermissionDeniedError,
    ModelRateLimitError,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.settings import Settings

logger = logging.getLogger(__name__)

# Clasificacion de errores del proveedor (langchain-google-genai / google-genai):
# - 429: `GoogleRateLimitError` (subclase de `langchain_core.exceptions.ModelRateLimitError`).
# - 5xx: `langchain_google_genai.chat_models.GoogleAPIError`, que hereda de
#   `google.genai.errors.ServerError` y expone el HTTP en `.code` (500/502/503/504) y el
#   estado en `.status` (p. ej. "UNAVAILABLE"). Es transitorio.
# - 4xx permanentes: `GoogleAuthenticationError` (401), `GooglePermissionDeniedError` (403),
#   `GoogleInvalidRequestError` (400), `GoogleModelNotFoundError` (404), es decir las
#   subclases de `ModelAuthenticationError`/`ModelPermissionDeniedError`/
#   `ModelInvalidRequestError`/`ModelNotFoundError`, y `google.genai.errors.ClientError`.
# Cualquier otra excepcion (p. ej. de validacion) no se toca: se propaga tal cual.
# - Red: `httpx.TransportError` (timeouts, conexion, lectura) llega sin envolver desde google-genai.
# - 408: `ClientError` code=408, que langchain envuelve en `ChatGoogleGenerativeAIError`
#   generico (el original queda en `__cause__`). Transitorio.
# - Resto de errores del proveedor (`ChatGoogleGenerativeAIError` generico: 409/413/422,
#   exceso de contexto...) son permanentes con mensaje neutro (RECHAZADA).
ErrorLimiteTasa = ModelRateLimitError
ERRORES_CONFIGURACION: tuple[type[BaseException], ...] = (
    ModelAuthenticationError,
    ModelPermissionDeniedError,
    ModelNotFoundError,
)
ERRORES_PROVEEDOR: tuple[type[BaseException], ...] = (
    ModelInvalidRequestError,
    ClientError,
    ChatGoogleGenerativeAIError,
)

MSG_TRANSITORIO = "El servicio del modelo está saturado o caído; inténtalo más tarde"
MSG_CONFIGURACION = "Error de configuración del modelo (clave o modelo inválidos)"
MSG_RECHAZADA = "El modelo rechazó la petición"

TRANSITORIO = "transitorio"
PERMANENTE = "permanente"  # configuracion: 401/403/404
RECHAZADA = "rechazada"  # cualquier otro error permanente del proveedor

_MENSAJES = {TRANSITORIO: MSG_TRANSITORIO, PERMANENTE: MSG_CONFIGURACION, RECHAZADA: MSG_RECHAZADA}


class LLMNoDisponible(RuntimeError):
    """El modelo no esta disponible: error transitorio persistente o error permanente.

    `motivo` es `TRANSITORIO` (reintentos agotados), `PERMANENTE` (clave/modelo invalidos)
    o `RECHAZADA` (otro rechazo del proveedor). El mensaje es generico: nunca incluye el
    cuerpo del proveedor ni secretos.
    """

    def __init__(self, mensaje: str | None = None, *, motivo: str = TRANSITORIO):
        self.motivo = motivo
        super().__init__(mensaje or self.mensaje_publico)

    @property
    def mensaje_publico(self) -> str:
        return _MENSAJES.get(self.motivo, MSG_TRANSITORIO)


def _codigo_http(error: BaseException) -> int | None:
    """Codigo HTTP del error o de su causa (langchain envuelve el ClientError original)."""
    for e in (error, error.__cause__):
        codigo = getattr(e, "code", None)
        if isinstance(codigo, int):
            return codigo
    return None


def clasificar_error(error: BaseException) -> str | None:
    """`TRANSITORIO` (429, 5xx, 408, red), `PERMANENTE`, `RECHAZADA` o None (ajeno)."""
    if isinstance(error, LLMNoDisponible):
        return None
    if isinstance(error, (ErrorLimiteTasa, httpx.TransportError)):
        return TRANSITORIO
    if isinstance(error, ServerError):
        codigo = getattr(error, "code", None)
        return TRANSITORIO if not isinstance(codigo, int) or codigo >= 500 else RECHAZADA
    if isinstance(error, ERRORES_PROVEEDOR + ERRORES_CONFIGURACION):
        codigo = _codigo_http(error)
        if codigo == 408:
            return TRANSITORIO
        if isinstance(error, ERRORES_CONFIGURACION) or codigo in (401, 403, 404):
            return PERMANENTE
        return RECHAZADA
    return None


class GeminiConReintentos(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI con reintentos y espera exponencial ante errores transitorios.

    Transitorios: 429 y 5xx. Al agotar los reintentos, o ante un error permanente,
    lanza `LLMNoDisponible`.
    """

    reintentos_429: int = 3
    espera_base_429: float = 2.0
    espera_max_429: float = 20.0

    def _espera(self, intento: int) -> float:
        return min(self.espera_base_429 * (2**intento), self.espera_max_429)

    def _decidir(self, error: Exception, intento: int) -> None:
        """Vuelve si hay que reintentar; lanza LLMNoDisponible si no; re-lanza si es ajeno."""
        tipo = clasificar_error(error)
        if tipo is None:
            raise error
        if tipo != TRANSITORIO:
            logger.error("Error permanente del modelo: %s", type(error).__name__)
            raise LLMNoDisponible(motivo=tipo) from error
        if intento >= self.reintentos_429:
            logger.error(
                "Modelo no disponible tras %d reintentos: %s", intento, type(error).__name__
            )
            raise LLMNoDisponible(motivo=TRANSITORIO) from error
        logger.warning(
            "Error transitorio del modelo (%s); reintento %d/%d",
            type(error).__name__, intento + 1, self.reintentos_429,
        )

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        intento = 0
        while True:
            try:
                return await super()._agenerate(messages, stop, run_manager, **kwargs)
            except Exception as e:
                self._decidir(e, intento)
                await asyncio.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    await self.rate_limiter.aacquire(blocking=True)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        intento = 0
        while True:
            try:
                return super()._generate(messages, stop, run_manager, **kwargs)
            except Exception as e:
                self._decidir(e, intento)
                time.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    self.rate_limiter.acquire(blocking=True)

    async def _astream(
        self, messages, stop=None, run_manager=None, **kwargs: Any
    ) -> AsyncIterator[ChatGenerationChunk]:
        # Solo se reintenta si el error llega antes del primer fragmento (no duplica salida).
        intento = 0
        while True:
            emitido = False
            try:
                async for chunk in super()._astream(messages, stop, run_manager, **kwargs):
                    emitido = True
                    yield chunk
                return
            except Exception as e:
                if emitido:
                    raise
                self._decidir(e, intento)
                await asyncio.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    await self.rate_limiter.aacquire(blocking=True)

    def _stream(self, messages, stop=None, run_manager=None, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        intento = 0
        while True:
            emitido = False
            try:
                for chunk in super()._stream(messages, stop, run_manager, **kwargs):
                    emitido = True
                    yield chunk
                return
            except Exception as e:
                if emitido:
                    raise
                self._decidir(e, intento)
                time.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    self.rate_limiter.acquire(blocking=True)


def crear_llm(
    settings: Settings,
    *,
    reintentos: int | None = None,
    espera_base: float | None = None,
    espera_max: float | None = None,
) -> BaseChatModel:
    """Construye el chat model de Gemini a partir de Settings.

    - Limite de tasa: `settings.gemini_rpm` peticiones por minuto (token bucket en memoria).
    - Reintentos: espera exponencial ante 429 y 5xx (valores de Settings salvo que se pasen
      explicitamente); al agotarlos, o ante un error permanente, lanza `LLMNoDisponible`.
    - Los reintentos internos del SDK se desactivan (`max_retries=1`) para que la unica
      politica de reintento sea la de este modulo.
    """
    limitador = InMemoryRateLimiter(
        requests_per_second=settings.gemini_rpm / 60.0,
        check_every_n_seconds=0.1,
        max_bucket_size=1,
    )
    return GeminiConReintentos(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        rate_limiter=limitador,
        max_retries=1,
        reintentos_429=settings.llm_reintentos if reintentos is None else reintentos,
        espera_base_429=settings.llm_espera_base if espera_base is None else espera_base,
        espera_max_429=settings.llm_espera_max if espera_max is None else espera_max,
    )
