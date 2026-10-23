"""Estado del grafo y esquemas Pydantic de las salidas estructuradas del LLM."""

from typing import Annotated, Literal, TypedDict
from uuid import UUID

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.domain.modelos import DiaRutina, Lesion, Nivel, Perfil, Rutina

Destino = Literal["programador", "progreso", "seguridad", "sintesis", "hitl"]


class EstadoCoach(TypedDict, total=False):
    # Entrada del turno
    usuario_id: UUID
    mensaje: str
    # Datos de dominio (Postgres es la fuente de verdad; se recargan en cada turno)
    perfil: Perfil | None
    lesiones: list[Lesion]
    rutina: Rutina | None
    # Control de seguridad del turno
    bloqueados: list[str]
    intentos_seguridad: int
    rutina_nueva: bool  # la rutina del estado aun no esta persistida (viene del programador/progreso)
    plan_validado: bool  # seguridad aprobo la rutina en este turno
    fallo_plan: bool  # el LLM no devolvio un plan utilizable
    retirados: list[str]  # ejercicios quitados de la rutina existente al revalidarla
    volumen: dict[str, int] | None  # series semanales por musculo del plan nuevo (volumen_semanal)
    lesion_nueva: bool
    requiere_humano: bool
    motivo_humano: str | None
    ejercicio_con_dolor: str | None
    explicacion: str
    siguiente: Destino | None
    respuesta: str | None
    # Persistente entre turnos (checkpointer)
    ejercicios_excluidos: list[str]
    mensajes: Annotated[list[AnyMessage], add_messages]


class PerfilParcial(BaseModel):
    objetivo: str | None = None
    dias_disponibles: int | None = Field(default=None, ge=1, le=7)
    equipo: list[str] | None = None
    nivel: Nivel | None = None


class AnalisisMensaje(BaseModel):
    """Salida estructurada del evaluador."""

    perfil: PerfilParcial | None = Field(
        default=None, description="Datos de perfil que el usuario menciona en este mensaje."
    )
    lesiones_nuevas: list[Lesion] = Field(
        default_factory=list, description=(
            "Lesiones nuevas que el usuario reporta en el mensaje actual (no las del historial "
            "ni las ya registradas)."
        ),
    )
    dolor_agudo: bool = Field(
        default=False,
        description=(
            "True solo si el mensaje actual reporta dolor agudo o dolor que empeora durante un "
            "ejercicio. False si el dolor solo aparece en mensajes anteriores."
        ),
    )
    ejercicio_con_dolor: str | None = Field(
        default=None, description="Id del ejercicio que le provoca dolor, si lo menciona en el mensaje actual."
    )


class DecisionSupervisor(BaseModel):
    destino: Destino
    motivo: str = ""


class PlanPropuesto(BaseModel):
    """Salida estructurada del programador y del agente de progreso."""

    dias: list[DiaRutina]
    explicacion: str = ""
