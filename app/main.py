"""Fabrica de la aplicacion FastAPI. Nada se construye al importar: todo va en el lifespan."""

import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.rutas import (
    TIMEOUT_SALUD_SEG, EjercicioDesconocido, NoEncontrado, ServicioNoDisponible,
    SinPausaPendiente, router,
)
from app.domain.modelos import Ejercicio
from app.llm import LLMNoDisponible
from app.safety.reglas import ReglasInvalidas, validar_reglas_contra_catalogo
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

Comprobacion = Callable[[], Awaitable[None]]


def _json(status: int, detalle: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detalle})


def _registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(LLMNoDisponible)
    async def _llm(_: Request, __: LLMNoDisponible):
        return _json(503, "El servicio de lenguaje no está disponible; inténtalo más tarde")

    @app.exception_handler(ServicioNoDisponible)
    async def _servicio(_: Request, exc: ServicioNoDisponible):
        return _json(503, exc.mensaje)

    @app.exception_handler(EjercicioDesconocido)
    async def _ejercicio(_: Request, exc: EjercicioDesconocido):
        return _json(422, f"ejercicio_id desconocido: '{exc.ejercicio_id}'")

    @app.exception_handler(NoEncontrado)
    async def _no_encontrado(_: Request, exc: NoEncontrado):
        return _json(404, exc.mensaje)

    @app.exception_handler(SinPausaPendiente)
    async def _sin_pausa(_: Request, __: SinPausaPendiente):
        return _json(409, "No hay una conversación pausada para reanudar")

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, exc: Exception):
        logger.exception("Error no controlado")
        return _json(500, "Error interno")


# Errores de configuracion que deben detener el arranque en vez de degradarlo.
# ReglasInvalidas: las reglas de seguridad no encajan con el catalogo (filtro fallaria abierto).
ERRORES_FATALES_ARRANQUE: tuple[type[BaseException], ...] = (ReglasInvalidas,)


def _crear_motor(url: str):
    from app.persistencia.repositorios import crear_motor

    return crear_motor(url)


@asynccontextmanager
async def _abrir_checkpointer(redis_url: str):
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
        await saver.asetup()
        yield saver


async def _construir_grafo(cfg, repo, saver, *, catalogo):
    from app.agentes.grafo import construir_grafo

    return await construir_grafo(cfg, repo, saver, catalogo=catalogo)


def _cargar_catalogo(settings: Settings) -> dict[str, Ejercicio] | None:
    from app.catalogo.cargador import cargar_catalogo

    try:
        catalogo = {e.id: e for e in cargar_catalogo(settings.catalogo_path)}
        # Reglas desalineadas con el catalogo dejarian pasar ejercicios de riesgo: no se arranca.
        validar_reglas_contra_catalogo(catalogo)
        return catalogo
    except ERRORES_FATALES_ARRANQUE:
        raise
    except Exception as exc:  # archivo ausente o catalogo invalido: las rutas responden 503
        logger.error("No se pudo cargar el catálogo: %s", type(exc).__name__)
        return None


def _comprobaciones(settings: Settings, motor) -> dict[str, Comprobacion]:
    async def postgres() -> None:
        async with motor.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def redis() -> None:
        from redis.asyncio import from_url

        cliente = from_url(settings.redis_url)
        try:
            await cliente.ping()
        finally:
            await cliente.aclose()

    async def qdrant() -> None:
        async with httpx.AsyncClient(timeout=TIMEOUT_SALUD_SEG) as http:
            r = await http.get(f"{settings.qdrant_url.rstrip('/')}/healthz")
            r.raise_for_status()

    return {"postgres": postgres, "redis": redis, "qdrant": qdrant}


@dataclass(frozen=True)
class Constructores:
    """Fabricas que usa el lifespan; se inyectan en pruebas para no depender de servicios."""

    motor: Callable[[str], Any] = _crear_motor
    checkpointer: Callable[[str], AbstractAsyncContextManager] = _abrir_checkpointer
    grafo: Callable[..., Awaitable[Any]] = _construir_grafo


def crear_app(
    settings: Settings | None = None,
    *,
    grafo=None,
    repo=None,
    catalogo: dict[str, Ejercicio] | None = None,
    comprobaciones: dict[str, Comprobacion] | None = None,
    constructores: Constructores | None = None,
) -> FastAPI:
    """Las dependencias inyectadas se usan tal cual; las ausentes se construyen en el lifespan.

    Si un servicio no se puede construir, la app arranca degradada (las rutas afectadas
    responden 503), salvo que el error sea de `ERRORES_FATALES_ARRANQUE`.
    """
    ctor = constructores or Constructores()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with AsyncExitStack() as pila:
            cfg = settings or get_settings()
            motor = None
            if app.state.repo is None:
                try:
                    from app.persistencia.repositorios import RepositorioDominio

                    motor = ctor.motor(cfg.database_url)
                    pila.push_async_callback(motor.dispose)
                    app.state.repo = RepositorioDominio(
                        async_sessionmaker(motor, expire_on_commit=False)
                    )
                except ERRORES_FATALES_ARRANQUE:
                    raise
                except Exception as exc:
                    logger.error("No se pudo construir el repositorio: %s", type(exc).__name__)
            if app.state.catalogo is None:
                app.state.catalogo = _cargar_catalogo(cfg)
            if app.state.comprobaciones is None and motor is not None:
                app.state.comprobaciones = _comprobaciones(cfg, motor)
            if (
                app.state.grafo is None
                and app.state.catalogo is not None
                and app.state.repo is not None
            ):
                try:
                    saver = await pila.enter_async_context(ctor.checkpointer(cfg.redis_url))
                    app.state.grafo = await ctor.grafo(
                        cfg, app.state.repo, saver, catalogo=app.state.catalogo
                    )
                except ERRORES_FATALES_ARRANQUE:
                    raise
                except Exception as exc:
                    logger.error("No se pudo construir el grafo: %s", type(exc).__name__)
            yield

    app = FastAPI(
        title="Coach de gimnasio", version="0.1.0", lifespan=lifespan,
        description="API del coach de gimnasio con IA (LangGraph, RAG híbrido y HITL).",
    )
    app.state.grafo = grafo
    app.state.repo = repo
    app.state.catalogo = catalogo
    app.state.comprobaciones = comprobaciones
    _registrar_manejadores(app)
    app.include_router(router)
    return app


app = crear_app()
