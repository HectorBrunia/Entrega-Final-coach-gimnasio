"""Ingiere el catalogo de ejercicios y las guias en Qdrant con los codificadores de produccion.

Uso: python scripts/ingerir.py [--forzar]

Todo se lee de Settings (entorno o .env): QDRANT_URL, QDRANT_COLLECTION, EMBEDDING_MODEL,
BM25_IDIOMA, CATALOGO_PATH y GUIAS_DIR. No necesita la clave de Gemini.

Idempotente:
- Los puntos tienen id determinista: reingestar sobrescribe, no duplica.
- La coleccion existente se verifica (vectores, dimension, IDF); si es incompatible se aborta
  con un mensaje que explica como recrearla (ColeccionIncompatible).
- Si la coleccion ya contiene exactamente los mismos documentos, no se recodifica nada
  (salvo con --forzar). Los puntos que ya no estan en el corpus se eliminan.

La primera ejecucion descarga los modelos de embeddings de Hugging Face.
"""

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import AsyncQdrantClient  # noqa: E402
from qdrant_client.models import PointIdsList  # noqa: E402

from app.catalogo.cargador import cargar_catalogo  # noqa: E402
from app.rag.codificadores import (  # noqa: E402
    CodificadorDenso,
    CodificadorDisperso,
    cliente_desde_settings,
    denso_desde_settings,
    en_hilo,
)
from app.rag.ingesta import (  # noqa: E402
    ColeccionIncompatible,
    Documento,
    asegurar_coleccion,
    documento_desde_ejercicio,
    documentos_desde_guias,
    ingerir,
    punto_id,
)
from app.settings import Settings, SettingsSinLLM  # noqa: E402

_LOTE_SCROLL = 256


@dataclass(frozen=True)
class ResumenIngesta:
    coleccion: str
    ejercicios: int
    fragmentos_guias: int
    reingestado: bool
    eliminados: int
    segundos: float


def documentos_corpus(settings: Settings) -> tuple[list[Documento], list[Documento]]:
    """(documentos del catalogo, fragmentos de las guias) segun las rutas de Settings."""
    ejercicios = [documento_desde_ejercicio(e) for e in cargar_catalogo(settings.catalogo_path)]
    guias = documentos_desde_guias(settings.guias_dir)
    if not guias:
        raise FileNotFoundError(f"No hay guias *.md en {settings.guias_dir}")
    return ejercicios, guias


async def _contenido_actual(cliente: AsyncQdrantClient, coleccion: str) -> dict[str, dict]:
    contenido: dict[str, dict] = {}
    desplazamiento = None
    while True:
        puntos, desplazamiento = await cliente.scroll(
            coleccion, limit=_LOTE_SCROLL, offset=desplazamiento,
            with_payload=True, with_vectors=False,
        )
        for p in puntos:
            contenido[str(p.id)] = p.payload or {}
        if desplazamiento is None:
            return contenido


def _payload(d: Documento) -> dict:
    return {"id": d.id, "texto": d.texto, "fuente": d.fuente, "metadatos": d.metadatos}


async def ingerir_corpus(
    settings: Settings,
    *,
    forzar: bool = False,
    cliente: AsyncQdrantClient | None = None,
    denso: CodificadorDenso | None = None,
    disperso: CodificadorDisperso | None = None,
) -> ResumenIngesta:
    inicio = time.perf_counter()
    ejercicios, guias = documentos_corpus(settings)
    documentos = ejercicios + guias
    esperado = {punto_id(d.id): _payload(d) for d in documentos}
    coleccion = settings.qdrant_collection

    propio = cliente is None
    cliente = cliente or cliente_desde_settings(settings)
    denso = denso or denso_desde_settings(settings)
    try:
        actual: dict[str, dict] = {}
        if await cliente.collection_exists(coleccion):
            # verifica la configuracion antes de nada: una coleccion incompatible aborta
            dim = len((await en_hilo(denso.codificar, ["dimension"]))[0])
            await asegurar_coleccion(cliente, coleccion, dim)
            actual = await _contenido_actual(cliente, coleccion)

        reingestado = forzar or actual != esperado
        if reingestado:
            await ingerir(documentos, settings, cliente=cliente, denso=denso, disperso=disperso)
        sobrantes = [pid for pid in actual if pid not in esperado]
        if sobrantes:
            await cliente.delete(coleccion, points_selector=PointIdsList(points=sobrantes), wait=True)
    finally:
        if propio:
            await cliente.close()
    return ResumenIngesta(
        coleccion=coleccion,
        ejercicios=len(ejercicios),
        fragmentos_guias=len(guias),
        reingestado=reingestado,
        eliminados=len(sobrantes),
        segundos=round(time.perf_counter() - inicio, 1),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="recodifica aunque no haya cambios")
    args = parser.parse_args()
    settings = SettingsSinLLM()
    try:
        r = asyncio.run(ingerir_corpus(settings, forzar=args.forzar))
    except ColeccionIncompatible as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    estado = "ingestado" if r.reingestado else "sin cambios (no se recodifico)"
    print(
        f"Coleccion '{r.coleccion}': {r.ejercicios} ejercicios + {r.fragmentos_guias} "
        f"fragmentos de guias; {estado}; {r.eliminados} puntos obsoletos eliminados; {r.segundos} s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
