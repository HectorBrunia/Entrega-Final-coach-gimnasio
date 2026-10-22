import json
from pathlib import Path

from pydantic import ValidationError

from app.domain.modelos import Ejercicio

# free-exercise-db usa niveles en inglés; se aceptan también los valores en español.
_NIVELES = {
    "beginner": "principiante",
    "intermediate": "intermedio",
    "expert": "avanzado",
}


class CatalogoInvalido(ValueError):
    """Un registro del catálogo no cumple el modelo Ejercicio."""


def _a_ejercicio(registro: dict) -> Ejercicio:
    nivel = str(registro.get("level", "")).strip().lower()
    equipo = registro.get("equipment")
    if equipo is None or str(equipo).strip().lower() == "body only":
        equipo = "cuerpo"
    primarios = registro.get("primaryMuscles") or [None]
    return Ejercicio(
        id=registro.get("id"),
        nombre=registro.get("name"),
        musculo_primario=primarios[0],
        musculos_secundarios=registro.get("secondaryMuscles", []),
        equipo=equipo,
        nivel=_NIVELES.get(nivel, nivel),
        instrucciones=registro.get("instructions", []),
    )


def cargar_catalogo(ruta: Path) -> list[Ejercicio]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    ejercicios: list[Ejercicio] = []
    for registro in datos:
        try:
            ejercicios.append(_a_ejercicio(registro))
        except (ValidationError, AttributeError, TypeError) as exc:
            id_ = registro.get("id") if isinstance(registro, dict) else registro
            raise CatalogoInvalido(f"Ejercicio inválido '{id_}': {exc}") from exc
    return ejercicios
