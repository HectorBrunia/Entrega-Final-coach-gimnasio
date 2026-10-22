"""Rutas de la API (spec sec. 8). Las dependencias viven en `request.app.state`."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from langgraph.types import Command

from app.agentes.grafo import config_hilo
from app.api.esquemas import (
    CrearUsuarioEntrada, EntrenoSalida, ErrorSalida, EstadoSalud, MensajeEntrada, MensajeSalida,
    PerfilSalida, ReanudarEntrada, RegistroEntrenoEntrada, RutinaSalida, UsuarioSalida,
)
from app.domain.modelos import EntrenoRegistro
from app.observabilidad import contexto_traza

logger = logging.getLogger(__name__)

TIMEOUT_SALUD_SEG = 2.0

router = APIRouter()


class ServicioNoDisponible(Exception):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class EjercicioDesconocido(Exception):
    def __init__(self, ejercicio_id: str):
        super().__init__(ejercicio_id)
        self.ejercicio_id = ejercicio_id


class NoEncontrado(Exception):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class SinPausaPendiente(Exception):
    pass


def _dep(request: Request, nombre: str, descripcion: str) -> Any:
    valor = getattr(request.app.state, nombre, None)
    if valor is None:
        raise ServicioNoDisponible(f"{descripcion} no disponible")
    return valor


def _respuesta_grafo(salida: dict, thread_id: str) -> MensajeSalida:
    interrupciones = salida.get("__interrupt__")
    if interrupciones:
        valor = getattr(interrupciones[0], "value", interrupciones[0])
        if isinstance(valor, str):
            texto = valor
        else:
            motivo = valor.get("motivo", "revisión") if isinstance(valor, dict) else "revisión"
            texto = (
                f"Conversación pausada para revisión humana ({motivo}). Detén ese ejercicio y "
                "consulta a un profesional de la salud. Esto no es un diagnóstico médico."
            )
        return MensajeSalida(respuesta=texto, requiere_humano=True, thread_id=thread_id)
    return MensajeSalida(
        respuesta=salida.get("respuesta") or "", requiere_humano=False, thread_id=thread_id
    )


@router.post("/usuarios", status_code=201, response_model=UsuarioSalida, tags=["usuarios"])
async def crear_usuario(
    request: Request,
    datos: CrearUsuarioEntrada = Body(default_factory=CrearUsuarioEntrada),
) -> UsuarioSalida:
    repo = _dep(request, "repo", "Base de datos")
    return UsuarioSalida(id=await repo.crear_usuario())


@router.post(
    "/chat", response_model=MensajeSalida, tags=["chat"],
    responses={503: {"model": ErrorSalida}},
)
async def chat(request: Request, entrada: MensajeEntrada) -> MensajeSalida:
    grafo = _dep(request, "grafo", "Coach")
    hilo = str(entrada.usuario_id)  # thread_id == str(usuario_id)
    logger.info("chat thread_id=%s usuario_id=%s", hilo, entrada.usuario_id)
    with contexto_traza("chat", thread_id=hilo, usuario_id=hilo):
        salida = await grafo.ainvoke(
            {"usuario_id": entrada.usuario_id, "mensaje": entrada.mensaje},
            config_hilo(entrada.usuario_id),
        )
    return _respuesta_grafo(salida, str(entrada.usuario_id))


@router.get(
    "/usuarios/{usuario_id}/perfil", response_model=PerfilSalida, tags=["usuarios"],
    responses={404: {"model": ErrorSalida}},
)
async def obtener_perfil(request: Request, usuario_id: UUID) -> PerfilSalida:
    repo = _dep(request, "repo", "Base de datos")
    perfil = await repo.obtener_perfil(usuario_id)
    if perfil is None:
        raise NoEncontrado("Perfil no encontrado")
    return PerfilSalida(**perfil.model_dump())


@router.post(
    "/usuarios/{usuario_id}/entrenos", status_code=201, response_model=EntrenoSalida,
    tags=["entrenos"], responses={422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}},
)
async def registrar_entreno(
    request: Request, usuario_id: UUID, entrada: RegistroEntrenoEntrada
) -> EntrenoSalida:
    catalogo = _dep(request, "catalogo", "Catálogo de ejercicios")
    if entrada.ejercicio_id not in catalogo:  # antes de cualquier llamada a la BD
        raise EjercicioDesconocido(entrada.ejercicio_id)
    repo = _dep(request, "repo", "Base de datos")
    await repo.registrar_entreno(EntrenoRegistro(usuario_id=usuario_id, **entrada.model_dump()))
    return EntrenoSalida(
        usuario_id=usuario_id, fecha=entrada.fecha, ejercicio_id=entrada.ejercicio_id
    )


@router.get(
    "/usuarios/{usuario_id}/rutinas/actual", response_model=RutinaSalida, tags=["rutinas"],
    responses={404: {"model": ErrorSalida}},
)
async def rutina_actual(request: Request, usuario_id: UUID) -> RutinaSalida:
    repo = _dep(request, "repo", "Base de datos")
    rutina = await repo.rutina_actual(usuario_id)
    if rutina is None:
        raise NoEncontrado("Rutina no encontrada")
    return RutinaSalida(**rutina.model_dump())


@router.post(
    "/hitl/{thread_id}/reanudar", response_model=MensajeSalida, tags=["chat"],
    responses={409: {"model": ErrorSalida}, 503: {"model": ErrorSalida}},
)
async def reanudar(request: Request, thread_id: UUID, entrada: ReanudarEntrada) -> MensajeSalida:
    grafo = _dep(request, "grafo", "Coach")
    config = config_hilo(thread_id)  # thread_id == str(usuario_id)
    estado = await grafo.aget_state(config)
    if not estado.next:
        raise SinPausaPendiente()
    logger.info("hitl thread_id=%s usuario_id=%s", thread_id, thread_id)
    with contexto_traza("hitl_reanudar", thread_id=str(thread_id), usuario_id=str(thread_id)):
        salida = await grafo.ainvoke(Command(resume=entrada.revision), config)
    return _respuesta_grafo(salida, str(thread_id))


async def _comprobar(fn: Callable[[], Awaitable[None]]) -> str:
    try:
        await asyncio.wait_for(fn(), timeout=TIMEOUT_SALUD_SEG)
        return "ok"
    except Exception as exc:  # el detalle va al log, nunca a la respuesta
        logger.warning("Health check fallido: %s", type(exc).__name__)
        return "error"


@router.get(
    "/health", response_model=EstadoSalud, tags=["salud"],
    responses={503: {"model": EstadoSalud}},
)
async def health(request: Request):
    comprobaciones: dict[str, Callable[[], Awaitable[None]]] = (
        getattr(request.app.state, "comprobaciones", None) or {}
    )
    nombres = ["postgres", "redis", "qdrant"]

    async def _no_configurada() -> None:
        raise RuntimeError("no configurado")

    resultados = await asyncio.gather(
        *(_comprobar(comprobaciones.get(n, _no_configurada)) for n in nombres)
    )
    servicios = dict(zip(nombres, resultados))
    ok = all(v == "ok" for v in servicios.values())
    estado = EstadoSalud(status="ok" if ok else "degradado", servicios=servicios)
    return JSONResponse(status_code=200 if ok else 503, content=estado.model_dump())
