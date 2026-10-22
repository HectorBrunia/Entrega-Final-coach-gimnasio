from datetime import date
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.equipo import normalizar_equipo


class Nivel(str, Enum):
    principiante = "principiante"
    intermedio = "intermedio"
    avanzado = "avanzado"


class Perfil(BaseModel):
    usuario_id: UUID
    objetivo: str
    dias_disponibles: int = Field(ge=1, le=7)
    equipo: list[str]
    nivel: Nivel

    @field_validator("equipo")
    @classmethod
    def _equipo_del_catalogo(cls, valor: list[str]) -> list[str]:
        # vocabulario canonico = el del catalogo; sinonimos en español mapeados, desconocidos fuera
        return normalizar_equipo(valor)


class Lesion(BaseModel):
    zona: str
    severidad: Literal["leve", "moderada", "grave"]
    activa: bool


class Ejercicio(BaseModel):
    id: str
    nombre: str
    musculo_primario: str
    musculos_secundarios: list[str]
    equipo: str
    nivel: Nivel
    instrucciones: list[str]


class EntrenoRegistro(BaseModel):
    usuario_id: UUID
    fecha: date
    ejercicio_id: str
    series: int = Field(ge=1)
    repeticiones: int = Field(ge=1)
    peso_kg: float = Field(ge=0)
    rpe: int = Field(ge=1, le=10)
    notas: str | None = None


class EjercicioPlanificado(BaseModel):
    ejercicio_id: str
    series: int = Field(ge=1)
    repeticiones: str
    descanso_seg: int = Field(ge=0)
    fuentes: list[str]


class DiaRutina(BaseModel):
    nombre: str
    ejercicios: list[EjercicioPlanificado]


class Rutina(BaseModel):
    usuario_id: UUID
    version: int
    dias: list[DiaRutina]
