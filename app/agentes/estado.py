"""Estado del grafo y esquemas Pydantic de las salidas estructuradas del LLM."""

from typing import Annotated, Literal, TypedDict
from uuid import UUID

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field

from app.domain.modelos import DiaRutina, Lesion, Nivel, Perfil, PerfilBorrador, Rutina
from app.safety.reglas import REGLAS_LESION

Destino = Literal["programador", "progreso", "seguridad", "sintesis", "hitl"]


class EstadoCoach(TypedDict, total=False):
    # Entrada del turno
    usuario_id: UUID
    mensaje: str
    # Datos de dominio (Postgres es la fuente de verdad; se recargan en cada turno)
    perfil: Perfil | None
    perfil_borrador: PerfilBorrador | None  # datos parciales mientras el perfil no esta completo
    perfil_completado: bool  # el perfil se completo en este turno (onboarding terminado)
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


# Zonas que el evaluador puede reportar: las que tienen regla, dos genericas sin lado (se
# expanden a ambos lados al guardar) y "otra" (texto libre; se guarda como zona sin regla y
# por tanto escala a humano).
ZONAS_GENERICAS: dict[str, tuple[str, ...]] = {
    "hombro": ("hombro_derecho", "hombro_izquierdo"),
    "rodilla": ("rodilla_derecha", "rodilla_izquierda"),
}
ZONA_OTRA = "otra"
ZonaReportada = Literal[(*sorted(REGLAS_LESION), *ZONAS_GENERICAS, ZONA_OTRA)]  # type: ignore[valid-type]


class LesionReportada(BaseModel):
    """Lesion tal como la reporta el evaluador (zona acotada); se expande a `Lesion` al guardar."""

    model_config = ConfigDict(from_attributes=True)

    zona: ZonaReportada = Field(description=(
        "Zona lesionada. Usa 'hombro' o 'rodilla' si no se indica el lado, y 'otra' (con "
        "descripcion) para cualquier zona que no este en la lista."
    ))
    descripcion: str | None = Field(
        default=None, description="Solo si zona es 'otra': la zona en pocas palabras (p. ej. cuello)."
    )
    severidad: Literal["leve", "moderada", "grave"]
    activa: bool = True


class AnalisisMensaje(BaseModel):
    """Salida estructurada del evaluador."""

    perfil: PerfilParcial | None = Field(
        default=None, description=(
            "Datos de perfil (objetivo, dias_disponibles, equipo, nivel) que el usuario da en el "
            "ULTIMO mensaje. Sustituyen a los guardados."
        ),
    )
    perfil_historial: PerfilParcial | None = Field(
        default=None, description=(
            "Datos de perfil que el usuario dio en mensajes ANTERIORES de la conversacion (no en "
            "el ultimo). Solo completan datos que faltan; nunca sustituyen a los guardados."
        ),
    )
    lesiones_nuevas: list[LesionReportada] = Field(
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
    zona_dolor: str | None = Field(
        default=None, description=(
            "Si dolor_agudo es true: zona del cuerpo del dolor del mensaje actual (p. ej. pecho, "
            "hombro, rodilla, espalda)."
        ),
    )
    cita_dolor: str | None = Field(
        default=None, description=(
            "Si dolor_agudo es true: fragmento copiado literalmente del mensaje actual donde el "
            "usuario reporta el dolor. Vacio si el dolor no esta en el mensaje actual."
        ),
    )
    sintoma_cardiaco: bool = Field(
        default=False,
        description=(
            "True solo si el mensaje actual describe un sintoma propio que puede ser una urgencia "
            "cardiaca o respiratoria (dolor, presion o pesadez en el pecho, falta de aire anormal, "
            "corazon desbocado o irregular, desmayo, sudor frio, dolor irradiado al brazo "
            "izquierdo o la mandibula). False para charla de entrenamiento: frecuencia cardiaca "
            "o zonas, pulso en reposo, tecnica de respiracion, mejorar el fondo, agujetas."
        ),
    )
    cita_sintoma: str | None = Field(
        default=None, description=(
            "Si sintoma_cardiaco es true: fragmento copiado literalmente del mensaje actual que "
            "describe el sintoma."
        ),
    )


class RespuestaConversacion(BaseModel):
    """Salida estructurada de la conversacion libre de la sintesis."""

    texto: str = Field(description="Respuesta al usuario, en español.")
    contiene_ejercicios: bool = Field(description=(
        "True si el texto recomienda o prescribe ejercicios concretos, series, repeticiones, "
        "cargas o una rutina. False si no."
    ))


class DecisionSupervisor(BaseModel):
    destino: Destino
    motivo: str = ""


class PlanPropuesto(BaseModel):
    """Salida estructurada del programador y del agente de progreso."""

    dias: list[DiaRutina]
    # Sin explicacion en texto libre: la respuesta con la rutina es determinista (spec 7).
