"""Vocabulario de equipo: el canonico es el del catalogo tal como lo carga `app.catalogo.cargador`.

El perfil se escribe en español ("barra", "mancuernas"), pero el catalogo (free-exercise-db) usa
valores en inglés. Este es el unico mapa de sinonimos; `Perfil` normaliza su equipo al validarse,
asi el filtro por equipo compara siempre en el vocabulario del catalogo.
"""

import logging
import unicodedata

logger = logging.getLogger(__name__)

# Valores de `Ejercicio.equipo` en el catalogo cargado ("body only" y null se cargan como "cuerpo").
EQUIPO_CATALOGO: frozenset[str] = frozenset({
    "barbell", "dumbbell", "machine", "cable", "kettlebells", "bands", "medicine ball",
    "exercise ball", "foam roll", "e-z curl bar", "other", "cuerpo",
})

# Equipo que no hace falta tener: los ejercicios con peso corporal siempre son posibles.
EQUIPO_SIEMPRE_DISPONIBLE = "cuerpo"

_GIMNASIO = ("barbell", "dumbbell", "machine", "cable", "e-z curl bar")

# Sinonimo normalizado (minusculas, sin tildes, espacios simples) -> valores canonicos.
SINONIMOS_EQUIPO: dict[str, tuple[str, ...]] = {
    **{s: ("barbell",) for s in ("barra", "barras", "barra olimpica", "barras olimpicas")},
    **{s: ("dumbbell",) for s in ("mancuerna", "mancuernas", "dumbbells")},
    **{s: ("machine",) for s in ("maquina", "maquinas", "machines")},
    **{s: ("cable",) for s in ("polea", "poleas", "cables", "maquina de poleas")},
    **{s: ("kettlebells",) for s in ("kettlebell", "pesa rusa", "pesas rusas")},
    **{s: ("bands",) for s in ("banda", "bandas", "banda elastica", "bandas elasticas",
                               "goma", "gomas", "liga", "ligas")},
    **{s: ("medicine ball",) for s in ("balon medicinal", "balones medicinales",
                                       "pelota medicinal")},
    **{s: ("exercise ball",) for s in ("fitball", "pelota de ejercicio", "pelota suiza",
                                       "bola suiza", "balon de ejercicio")},
    **{s: ("foam roll",) for s in ("rodillo", "rodillo de espuma", "foam roller")},
    **{s: ("e-z curl bar",) for s in ("barra z", "barra ez", "barra e-z", "ez bar")},
    **{s: ("cuerpo",) for s in ("peso corporal", "sin equipo", "ninguno", "nada",
                                "body only", "calistenia")},
    **{s: ("other",) for s in ("otro", "otros")},
    **{s: _GIMNASIO for s in ("gimnasio", "gimnasio completo", "gym")},
}


# Nombre en español de cada valor canonico (para mostrar al usuario lo que ya se sabe).
NOMBRES_EQUIPO: dict[str, str] = {
    "barbell": "barra", "dumbbell": "mancuernas", "machine": "máquinas", "cable": "poleas",
    "kettlebells": "pesas rusas", "bands": "bandas elásticas", "medicine ball": "balón medicinal",
    "exercise ball": "fitball", "foam roll": "rodillo de espuma", "e-z curl bar": "barra Z",
    "other": "otro", "cuerpo": "peso corporal",
}


def describir_equipo(equipo: list[str]) -> str:
    """Equipo canonico en español, separado por comas."""
    return ", ".join(NOMBRES_EQUIPO.get(e, e) for e in equipo)


def _clave(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().replace("_", " ").split())


def normalizar_equipo(equipo: list[str]) -> list[str]:
    """Lleva cada elemento al vocabulario del catalogo, sin duplicados y en orden.

    Un elemento desconocido se registra en el log y se ignora (nunca hace fallar el perfil).
    """
    resultado: list[str] = []
    for item in equipo:
        clave = _clave(item)
        if clave in EQUIPO_CATALOGO:
            canonicos: tuple[str, ...] = (clave,)
        elif clave in SINONIMOS_EQUIPO:
            canonicos = SINONIMOS_EQUIPO[clave]
        else:
            logger.warning("Equipo desconocido ignorado: %r", item)
            continue
        resultado.extend(c for c in canonicos if c not in resultado)
    return resultado
