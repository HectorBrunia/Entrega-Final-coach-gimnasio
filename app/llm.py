"""Fabrica del LLM (Gemini) con limite de tasa y reintentos ante HTTP 429."""

import asyncio
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.exceptions import ModelRateLimitError
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from app.settings import Settings

# langchain-google-genai traduce el HTTP 429 del SDK google-genai (ClientError code=429)
# a `langchain_google_genai.chat_models.GoogleRateLimitError`, subclase de
# `langchain_core.exceptions.ModelRateLimitError`. Solo esa familia se reintenta.
ErrorLimiteTasa = ModelRateLimitError


class LLMNoDisponible(RuntimeError):
    """El proveedor sigue limitando la tasa (429) tras agotar los reintentos."""


class GeminiConReintentos(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI que reintenta con espera exponencial solo ante HTTP 429."""

    reintentos_429: int = 4
    espera_base_429: float = 2.0
    espera_max_429: float = 30.0

    def _espera(self, intento: int) -> float:
        return min(self.espera_base_429 * (2**intento), self.espera_max_429)

    def _agotado(self, _error: Exception) -> LLMNoDisponible:
        return LLMNoDisponible(
            f"Gemini sigue limitando la tasa tras {self.reintentos_429} reintentos"
        )

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        intento = 0
        while True:
            try:
                return await super()._agenerate(messages, stop, run_manager, **kwargs)
            except ErrorLimiteTasa as e:
                if intento >= self.reintentos_429:
                    raise self._agotado(e) from e
                await asyncio.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    await self.rate_limiter.aacquire(blocking=True)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        intento = 0
        while True:
            try:
                return super()._generate(messages, stop, run_manager, **kwargs)
            except ErrorLimiteTasa as e:
                if intento >= self.reintentos_429:
                    raise self._agotado(e) from e
                time.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    self.rate_limiter.acquire(blocking=True)

    async def _astream(
        self, messages, stop=None, run_manager=None, **kwargs: Any
    ) -> AsyncIterator[ChatGenerationChunk]:
        # Solo se reintenta si el 429 llega antes del primer fragmento (no duplica salida).
        intento = 0
        while True:
            emitido = False
            try:
                async for chunk in super()._astream(messages, stop, run_manager, **kwargs):
                    emitido = True
                    yield chunk
                return
            except ErrorLimiteTasa as e:
                if emitido:
                    raise
                if intento >= self.reintentos_429:
                    raise self._agotado(e) from e
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
            except ErrorLimiteTasa as e:
                if emitido:
                    raise
                if intento >= self.reintentos_429:
                    raise self._agotado(e) from e
                time.sleep(self._espera(intento))
                intento += 1
                if self.rate_limiter is not None:
                    self.rate_limiter.acquire(blocking=True)


def crear_llm(
    settings: Settings,
    *,
    reintentos: int = 4,
    espera_base: float = 2.0,
    espera_max: float = 30.0,
) -> BaseChatModel:
    """Construye el chat model de Gemini a partir de Settings.

    - Limite de tasa: `settings.gemini_rpm` peticiones por minuto (token bucket en memoria).
    - Reintentos: espera exponencial solo ante 429; al agotarlos lanza `LLMNoDisponible`.
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
        reintentos_429=reintentos,
        espera_base_429=espera_base,
        espera_max_429=espera_max,
    )
