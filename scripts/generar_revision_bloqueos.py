"""Genera docs/revision/bloqueos-por-zona.md: que bloquea cada regla de lesion sobre el catalogo real.

Uso (desde la raiz del repositorio):
    python scripts/generar_revision_bloqueos.py [ruta_catalogo] [ruta_salida]
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.catalogo.cargador import cargar_catalogo  # noqa: E402
from app.safety.reglas import (  # noqa: E402
    REGLAS_LESION,
    motivos_bloqueo,
    validar_reglas_contra_catalogo,
)

CATALOGO_POR_DEFECTO = RAIZ / "data" / "catalogo" / "exercises.json"
SALIDA_POR_DEFECTO = RAIZ / "docs" / "revision" / "bloqueos-por-zona.md"


def _celda(texto: str) -> str:
    return texto.replace("|", "\\|")


def generar(ruta_catalogo: Path) -> tuple[str, dict[str, int]]:
    """Devuelve el Markdown y el total bloqueado por zona."""
    ejercicios = sorted(cargar_catalogo(ruta_catalogo), key=lambda e: e.id)
    validar_reglas_contra_catalogo({e.id: e for e in ejercicios})
    zonas = sorted(REGLAS_LESION)
    bloqueos = {
        zona: [(e, m) for e in ejercicios if (m := motivos_bloqueo(e, REGLAS_LESION[zona]))]
        for zona in zonas
    }

    lineas = [
        "# Bloqueos por zona de lesión",
        "",
        "> **Pendiente de revisión por el usuario.**",
        "",
        "Este documento se genera con `python scripts/generar_revision_bloqueos.py` a partir de las",
        "reglas de `app/safety/reglas.py` y del catálogo real (`data/catalogo/exercises.json`,",
        f"free-exercise-db, {len(ejercicios)} ejercicios). No se edita a mano: si cambian las reglas",
        "o el catálogo, se vuelve a generar.",
        "",
        "Las reglas son deterministas y conservadoras (ante la duda, se bloquea). Un ejercicio queda",
        "bloqueado para una zona si cumple **cualquiera** de estos motivos:",
        "",
        "- **músculo**: alguno de sus músculos primario o secundarios está en la regla de la zona.",
        "- **patrón**: el patrón aparece en el id o en el nombre, sin distinguir mayúsculas ni",
        "  separadores (`upright row` bloquea `Upright_Row` y `Upright-Row`).",
        "- **id extra**: el id está en la lista explícita de la zona.",
        "",
        "Solo las lesiones con `activa=True` aplican, y una zona activa sin regla bloquea todo el",
        "proceso (falla cerrado). Por favor, revisa sobre todo dos cosas: ejercicios de riesgo que",
        "**no** aparezcan aquí (falsos negativos) y bloqueos que te parezcan excesivos.",
        "",
        "## Resumen",
        "",
        "| Zona | Bloqueados | Permitidos |",
        "|---|---:|---:|",
    ]
    for zona in zonas:
        n = len(bloqueos[zona])
        lineas.append(f"| `{zona}` | {n} | {len(ejercicios) - n} |")

    for zona in zonas:
        regla = REGLAS_LESION[zona]
        lineas += [
            "",
            f"## `{zona}` ({len(bloqueos[zona])} bloqueados)",
            "",
            f"- Músculos: {', '.join(sorted(regla.musculos)) or '(ninguno)'}",
            f"- Patrones: {', '.join(f'`{p}`' for p in regla.patrones_nombre) or '(ninguno)'}",
            f"- Ids extra: {', '.join(sorted(regla.ids_extra)) or '(ninguno)'}",
            "",
            "| Id | Nombre | Músculo primario | Motivo |",
            "|---|---|---|---|",
        ]
        for e, motivos in bloqueos[zona]:
            lineas.append(
                f"| `{e.id}` | {_celda(e.nombre)} | {e.musculo_primario} | {_celda('; '.join(motivos))} |"
            )
    return "\n".join(lineas) + "\n", {z: len(bloqueos[z]) for z in zonas}


def main(argv: list[str]) -> None:
    ruta_catalogo = Path(argv[1]) if len(argv) > 1 else CATALOGO_POR_DEFECTO
    salida = Path(argv[2]) if len(argv) > 2 else SALIDA_POR_DEFECTO
    salida.parent.mkdir(parents=True, exist_ok=True)
    texto, totales = generar(ruta_catalogo)
    salida.write_text(texto, encoding="utf-8", newline="\n")
    print(f"Escrito {salida}")
    for zona, total in totales.items():
        print(f"  {zona}: {total} bloqueados")


if __name__ == "__main__":
    main(sys.argv)
