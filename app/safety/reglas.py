from pydantic import BaseModel

from app.domain.modelos import Ejercicio, Lesion

_HOMBRO = frozenset({"press_militar", "elevaciones_frontales"})

# Contraindicaciones deterministas (spec 7). Zona exacta -> ejercicio_id bloqueados.
# Zona activa sin regla: falla cerrado (ZonaLesionDesconocida); el llamador escala a revision humana.
REGLAS_LESION: dict[str, frozenset[str]] = {
    "hombro_derecho": _HOMBRO,
    "hombro_izquierdo": _HOMBRO,
}


class ZonaLesionDesconocida(Exception):
    """Lesion activa cuya zona no tiene regla: el filtro falla cerrado."""


def _normalizar(zona: str) -> str:
    return zona.strip().lower()


_REGLAS_NORM: dict[str, frozenset[str]] = {_normalizar(k): v for k, v in REGLAS_LESION.items()}


class FiltroResultado(BaseModel):
    permitidos: list[Ejercicio]
    bloqueados: list[tuple[str, str]]  # (ejercicio_id, zona)


def filtrar_por_lesiones(ejercicios: list[Ejercicio], lesiones: list[Lesion]) -> FiltroResultado:
    zonas = [_normalizar(les.zona) for les in lesiones if les.activa]
    for z in zonas:
        if z not in _REGLAS_NORM:
            raise ZonaLesionDesconocida(f"Zona de lesion sin regla de seguridad: {z!r}")
    permitidos: list[Ejercicio] = []
    bloqueados: list[tuple[str, str]] = []
    for ej in ejercicios:
        zonas_bloqueantes = [z for z in dict.fromkeys(zonas) if ej.id in _REGLAS_NORM[z]]
        if zonas_bloqueantes:
            bloqueados.extend((ej.id, z) for z in zonas_bloqueantes)
        else:
            permitidos.append(ej)
    return FiltroResultado(permitidos=permitidos, bloqueados=bloqueados)
