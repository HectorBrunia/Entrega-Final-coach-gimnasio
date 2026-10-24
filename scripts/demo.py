"""Demo sin Docker, sin red y sin clave de Gemini: python scripts/demo.py

Ejecuta cinco escenarios sobre el grafo LangGraph real, con el catalogo y las reglas de
seguridad reales, y un LLM simulado (salidas estructuradas fijas por paso). Ver app/demo/.
Codigo de salida 0 si todas las comprobaciones pasan; 1 si alguna falla.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.demo.escenarios import ejecutar_demo  # noqa: E402


def main() -> int:
    # Salida redirigida (p. ej. a un archivo o a otro proceso): UTF-8. En consola se deja la
    # codificacion de la consola. Nunca falla por un caracter no representable.
    for flujo in (sys.stdout, sys.stderr):
        try:
            if flujo.isatty():
                flujo.reconfigure(errors="replace")
            else:
                flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    logging.basicConfig(level=logging.ERROR)
    resultado = asyncio.run(ejecutar_demo())
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
