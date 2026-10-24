"""Grafo LangGraph del coach: supervisor, especialistas, seguridad, HITL y sintesis."""

import asyncio
from collections.abc import Mapping
from typing import Any, Literal
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agentes.estado import EstadoCoach
from app.agentes.nodos import Buscador, Nodos
from app.domain.modelos import Ejercicio
from app.herramientas.funciones import buscar_conocimiento
from app.llm import crear_llm
from app.persistencia.repositorios import RepositorioDominio
from app.rag.ingesta import Documento, fuentes_de_guias
from app.rag.recuperador import FiltrosBusqueda
from app.safety.reglas import indice_bloqueo
from app.settings import Settings

# Limite duro de pasos por invocacion (recursion_limit de LangGraph). Un turno normal usa
# menos de 10; el bucle seguridad -> programador esta acotado ademas por max_reintentos.
LIMITE_PASOS = 25


def ruta_seguridad(
    estado: Mapping[str, Any], max_intentos: int
) -> Literal["programador", "sintesis", "hitl"]:
    """Decide la salida del nodo de seguridad. Funcion pura.

    requiere_humano se evalua primero: el dolor agudo o una zona sin regla siempre
    escalan a humano, aunque haya ejercicios bloqueados pendientes.
    """
    if estado.get("requiere_humano"):
        return "hitl"
    if estado.get("bloqueados"):
        if estado.get("intentos_seguridad", 0) < max_intentos:
            return "programador"
        return "sintesis"  # la sintesis responde que no hay plan seguro
    return "sintesis"


def ruta_supervisor(estado: Mapping[str, Any]) -> str:
    return estado.get("siguiente") or "sintesis"


def config_hilo(usuario_id: UUID) -> RunnableConfig:
    """Config de invocacion: el thread_id del checkpointer es el usuario."""
    return {"configurable": {"thread_id": str(usuario_id)}}


async def construir_grafo(
    settings: Settings,
    repo: RepositorioDominio,
    checkpointer: BaseCheckpointSaver,
    *,
    catalogo: dict[str, Ejercicio],
    llm: BaseChatModel | None = None,
    buscador: Buscador | None = None,
) -> CompiledStateGraph:
    if llm is None:
        llm = crear_llm(settings)
    if buscador is None:
        async def buscador(consulta: str, filtros: FiltrosBusqueda) -> list[Documento]:
            return await buscar_conocimiento(consulta, filtros, settings=settings)

    # indice zona -> ids bloqueados: se calcula una vez y fuera del event loop (CPU)
    indice = await asyncio.to_thread(indice_bloqueo, catalogo)
    fuentes_guia = await asyncio.to_thread(fuentes_de_guias, settings.guias_dir)
    nodos = Nodos(repo, catalogo, llm, buscador, indice, fuentes_guia=fuentes_guia)
    g = StateGraph(EstadoCoach)
    g.add_node("evaluador", nodos.evaluador)
    g.add_node("supervisor", nodos.supervisor)
    g.add_node("programador", nodos.programador)
    g.add_node("progreso", nodos.progreso)
    g.add_node("seguridad", nodos.seguridad)
    g.add_node("hitl", nodos.hitl)
    g.add_node("sintesis", nodos.sintesis)

    g.add_edge(START, "evaluador")
    g.add_edge("evaluador", "supervisor")
    g.add_conditional_edges(
        "supervisor", ruta_supervisor,
        ["programador", "progreso", "seguridad", "sintesis", "hitl"],
    )
    # todo plan nuevo o ajustado pasa por seguridad antes de llegar al usuario
    g.add_edge("programador", "seguridad")
    g.add_edge("progreso", "seguridad")
    g.add_conditional_edges(
        "seguridad",
        lambda e: ruta_seguridad(e, settings.max_reintentos_seguridad),
        ["programador", "sintesis", "hitl"],
    )
    g.add_edge("hitl", END)
    g.add_edge("sintesis", END)

    compilado = g.compile(checkpointer=checkpointer)
    return compilado.with_config(recursion_limit=LIMITE_PASOS)
