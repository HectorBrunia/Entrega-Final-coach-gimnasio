"""Modelos Pydantic de entrada y salida de la API (con ejemplos para OpenAPI)."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.modelos import DiaRutina, Nivel

_UID = "3f2b8c1e-5d4a-4e6b-9a7c-1d2e3f4a5b6c"


class CrearUsuarioEntrada(BaseModel):
    """Alta de usuario: no requiere datos; el perfil se completa conversando con el coach."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})


class UsuarioSalida(BaseModel):
    id: UUID

    model_config = ConfigDict(json_schema_extra={"examples": [{"id": _UID}]})


class MensajeEntrada(BaseModel):
    usuario_id: UUID
    mensaje: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"usuario_id": _UID, "mensaje": "Quiero una rutina de 4 días para ganar masa"}
    ]})


class MensajeSalida(BaseModel):
    respuesta: str
    requiere_humano: bool
    thread_id: str

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"respuesta": "Aquí tienes tu rutina. Esto no es un diagnóstico médico.",
         "requiere_humano": False, "thread_id": _UID},
        {"respuesta": "Conversación pausada para revisión humana (dolor_agudo).",
         "requiere_humano": True, "thread_id": _UID},
    ]})


class PerfilSalida(BaseModel):
    usuario_id: UUID
    objetivo: str
    dias_disponibles: int = Field(ge=1, le=7)
    equipo: list[str]
    nivel: Nivel

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"usuario_id": _UID, "objetivo": "masa muscular", "dias_disponibles": 4,
         "equipo": ["dumbbell", "barbell"], "nivel": "principiante"}
    ]})


class RegistroEntrenoEntrada(BaseModel):
    fecha: date
    ejercicio_id: str = Field(min_length=1)
    series: int = Field(ge=1)
    repeticiones: int = Field(ge=1)
    peso_kg: float = Field(ge=0)
    rpe: int = Field(ge=1, le=10)
    notas: str | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"fecha": "2026-10-01", "ejercicio_id": "sentadilla", "series": 3, "repeticiones": 8,
         "peso_kg": 60.0, "rpe": 7, "notas": None}
    ]})


class EntrenoSalida(BaseModel):
    usuario_id: UUID
    fecha: date
    ejercicio_id: str

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"usuario_id": _UID, "fecha": "2026-10-01", "ejercicio_id": "sentadilla"}
    ]})


class RutinaSalida(BaseModel):
    usuario_id: UUID
    version: int
    dias: list[DiaRutina]
    # Nombre legible de cada ejercicio_id de la rutina (lo usa el chat web para la tabla)
    nombres: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"usuario_id": _UID, "version": 1, "dias": [{
            "nombre": "Día 1",
            "ejercicios": [{"ejercicio_id": "sentadilla", "series": 3, "repeticiones": "8-10",
                            "descanso_seg": 90, "fuentes": ["catalogo"]}]}],
         "nombres": {"sentadilla": "Sentadilla"}}
    ]})


class ReanudarEntrada(BaseModel):
    revision: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"revision": "Revisado por un profesional; continuar sin ese ejercicio"}
    ]})


class EstadoSalud(BaseModel):
    status: Literal["ok", "degradado"]
    servicios: dict[str, str]
    # Informativo: si el coach conversacional (Gemini) esta configurado. No afecta al codigo
    # HTTP (200/503), que depende solo de postgres, redis y qdrant.
    llm: Literal["configurado", "no_configurado"] | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"status": "ok", "servicios": {"postgres": "ok", "redis": "ok", "qdrant": "ok"},
         "llm": "configurado"},
        {"status": "ok", "servicios": {"postgres": "ok", "redis": "ok", "qdrant": "ok"},
         "llm": "no_configurado"},
        {"status": "degradado",
         "servicios": {"postgres": "ok", "redis": "error", "qdrant": "ok"}},
    ]})


class ErrorSalida(BaseModel):
    detail: str

    model_config = ConfigDict(json_schema_extra={"examples": [{"detail": "Recurso no encontrado"}]})
