from pydantic import BaseModel

from app.domain.modelos import Ejercicio, Lesion

_HOMBRO = frozenset({"press_militar", "elevaciones_frontales"})

# Contraindicaciones deterministas (spec 7). Zona exacta -> ejercicio_id bloqueados.
# Zonas ausentes no bloquean nada (brecha conocida hasta curar las reglas completas).
REGLAS_LESION: dict[str, frozenset[str]] = {
    "hombro_derecho": _HOMBRO,
    "hombro_izquierdo": _HOMBRO,
}


class FiltroResultado(BaseModel):
    permitidos: list[Ejercicio]
    bloqueados: list[tuple[str, str]]  # (ejercicio_id, zona)


def filtrar_por_lesiones(ejercicios: list[Ejercicio], lesiones: list[Lesion]) -> FiltroResultado:
    zonas = [l.zona for l in lesiones if l.activa]
    permitidos: list[Ejercicio] = []
    bloqueados: list[tuple[str, str]] = []
    for ej in ejercicios:
        zonas_bloqueantes = [z for z in dict.fromkeys(zonas) if ej.id in REGLAS_LESION.get(z, frozenset())]
        if zonas_bloqueantes:
            bloqueados.extend((ej.id, z) for z in zonas_bloqueantes)
        else:
            permitidos.append(ej)
    return FiltroResultado(permitidos=permitidos, bloqueados=bloqueados)
