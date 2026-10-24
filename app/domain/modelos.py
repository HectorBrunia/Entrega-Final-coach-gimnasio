import re
import unicodedata
from datetime import date
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.equipo import normalizar_equipo


# Campos de la rutina que se muestran literalmente al usuario: forma estricta. La propuesta del
# LLM que no la cumpla no valida (el plan se rechaza); al mostrar una rutina ya guardada se
# sanea igual (ver app.agentes.nodos).
_REPETICIONES = re.compile(r"^\d{1,2}(?:-\d{1,2})?$")
MAX_NOMBRE_DIA = 40
_NOMBRE_DIA_PROHIBIDO = re.compile(
    r"^\s*(?:[-*•·>]|\d+\s*[.)])"                                   # marca de lista
    r"|\d+\s*(?:kg|kilos?|lbs?|x|×|series|sets?|reps?|repeticiones|tandas?|por\s*\d)"
    r"|\b(?:haz|hazlo|anade|agrega|incluye|realiza|ademas|tambien|luego|despues)\b"
)


def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def repeticiones_validas(valor: str) -> bool:
    """Repeticiones de un ejercicio planificado: un numero o un rango "N-M" (1-2 cifras)."""
    return bool(_REPETICIONES.match(valor or ""))


def nombre_dia_valido(nombre: str) -> bool:
    """Nombre de dia corto (<= MAX_NOMBRE_DIA), de una linea, sin marcas de lista, cargas,
    series o indicaciones ("Dia 1: ademas haz press militar 5x5" no vale)."""
    nombre = nombre or ""
    if not nombre.strip() or len(nombre) > MAX_NOMBRE_DIA or "\n" in nombre or "\r" in nombre:
        return False
    return not _NOMBRE_DIA_PROHIBIDO.search(_sin_tildes(nombre))


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


class PerfilBorrador(BaseModel):
    """Perfil en construccion: los datos que el usuario ya dio, repartidos en varios mensajes.

    Todos los campos son opcionales. Se persiste hasta que valida como `Perfil` completo;
    entonces se guarda el perfil y el borrador se borra. `equipo` ya va normalizado al
    vocabulario del catalogo (un equipo vacio cuenta como dato que falta).
    """

    objetivo: str | None = None
    dias_disponibles: int | None = Field(default=None, ge=1, le=7)
    equipo: list[str] | None = None
    nivel: Nivel | None = None


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
