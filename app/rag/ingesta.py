import re
import unicodedata
import uuid
from pathlib import Path

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    Modifier,
    PayloadSchemaType,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

from app.domain.modelos import Ejercicio
from app.rag.codificadores import (
    VECTOR_DENSO,
    VECTOR_DISPERSO,
    CodificadorDenso,
    CodificadorDisperso,
    cliente_desde_settings,
    denso_desde_settings,
    disperso_desde_settings,
    en_hilo,
)
from app.settings import Settings

CAMPOS_FILTRO = ("equipo", "nivel", "musculo")
_NAMESPACE = uuid.UUID("6f1c1c0e-3a6e-4c52-9d0e-5b1a8f0f7a11")


class Documento(BaseModel):
    id: str
    texto: str
    fuente: str
    metadatos: dict[str, str]


def punto_id(doc_id: str) -> str:
    """UUID determinista: reingestar el mismo documento sobrescribe el punto."""
    return str(uuid.uuid5(_NAMESPACE, doc_id))


def documento_desde_ejercicio(e: Ejercicio) -> Documento:
    texto = f"{e.nombre}. Músculo: {e.musculo_primario}. " + " ".join(e.instrucciones)
    return Documento(
        id=e.id,
        texto=texto,
        fuente="catalogo",
        metadatos={
            "equipo": e.equipo,
            "nivel": e.nivel.value,
            "musculo": e.musculo_primario,
        },
    )


PREFIJO_FUENTE_GUIA = "guia:"
_SECCIONES_EXCLUIDAS = {"fuentes"}  # bibliografia: no aporta contenido recuperable


def _slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def documentos_desde_guia(nombre: str, markdown: str) -> list[Documento]:
    """Trocea una guia Markdown por secciones `## ...`: un Documento por seccion.

    id = "<nombre>#<slug-seccion>", fuente = "guia:<nombre>", sin metadatos de filtro (las
    guias aplican a cualquier equipo, nivel o musculo). Se omite la seccion de fuentes.
    """
    titulo = nombre
    docs: list[Documento] = []
    seccion: str | None = None
    lineas: list[str] = []

    def _cerrar() -> None:
        cuerpo = "\n".join(lineas).strip()
        if seccion and cuerpo and _slug(seccion) not in _SECCIONES_EXCLUIDAS:
            docs.append(Documento(
                id=f"{nombre}#{_slug(seccion)}",
                texto=f"{titulo}. {seccion}.\n{cuerpo}",
                fuente=f"{PREFIJO_FUENTE_GUIA}{nombre}",
                metadatos={},
            ))

    for linea in markdown.splitlines():
        if linea.startswith("# "):
            titulo = linea[2:].strip()
        elif linea.startswith("## "):
            _cerrar()
            seccion, lineas = linea[3:].strip(), []
        elif seccion is not None:
            lineas.append(linea)
    _cerrar()
    return docs


def documentos_desde_guias(directorio: Path) -> list[Documento]:
    """Documentos de todas las guias `*.md` del directorio, en orden de nombre de archivo."""
    docs: list[Documento] = []
    for ruta in sorted(Path(directorio).glob("*.md")):
        docs.extend(documentos_desde_guia(ruta.stem, ruta.read_text(encoding="utf-8")))
    return docs


class ColeccionIncompatible(RuntimeError):
    """La coleccion existente no tiene la configuracion de vectores esperada."""


async def _verificar_config(cliente: AsyncQdrantClient, nombre: str, dim: int) -> None:
    params = (await cliente.get_collection(nombre)).config.params
    problemas = []
    densos = params.vectors if isinstance(params.vectors, dict) else {}
    if VECTOR_DENSO not in densos:
        problemas.append(f"falta el vector denso '{VECTOR_DENSO}'")
    elif densos[VECTOR_DENSO].size != dim:
        problemas.append(f"vector denso de tamano {densos[VECTOR_DENSO].size}, se esperaba {dim}")
    dispersos = params.sparse_vectors or {}
    if VECTOR_DISPERSO not in dispersos:
        problemas.append(f"falta el vector disperso '{VECTOR_DISPERSO}'")
    elif dispersos[VECTOR_DISPERSO].modifier != Modifier.IDF:
        problemas.append("el vector disperso no usa el modificador IDF")
    if problemas:
        raise ColeccionIncompatible(
            f"La coleccion '{nombre}' es incompatible ({'; '.join(problemas)}). "
            "Eliminala (drop) y vuelve a ejecutar la ingesta."
        )


async def asegurar_coleccion(cliente: AsyncQdrantClient, nombre: str, dim: int) -> None:
    """Crea la coleccion si no existe; si existe, verifica que su configuracion sea compatible."""
    if not await cliente.collection_exists(nombre):
        try:
            await cliente.create_collection(
                nombre,
                vectors_config={VECTOR_DENSO: VectorParams(size=dim, distance=Distance.COSINE)},
                sparse_vectors_config={VECTOR_DISPERSO: SparseVectorParams(modifier=Modifier.IDF)},
            )
        except Exception:
            # carrera con otro proceso: si ya existe, se verifica abajo
            if not await cliente.collection_exists(nombre):
                raise
    await _verificar_config(cliente, nombre, dim)
    for campo in CAMPOS_FILTRO:
        await cliente.create_payload_index(
            nombre, f"metadatos.{campo}", PayloadSchemaType.KEYWORD
        )


async def ingerir(
    documentos: list[Documento],
    settings: Settings,
    *,
    cliente: AsyncQdrantClient | None = None,
    denso: CodificadorDenso | None = None,
    disperso: CodificadorDisperso | None = None,
) -> None:
    if not documentos:
        return
    propio = cliente is None
    cliente = cliente or cliente_desde_settings(settings)
    denso = denso or denso_desde_settings(settings)
    disperso = disperso or disperso_desde_settings(settings)
    try:
        textos = [d.texto for d in documentos]
        vec_densos = await en_hilo(denso.codificar, textos)
        vec_dispersos = await en_hilo(disperso.codificar, textos)
        await asegurar_coleccion(cliente, settings.qdrant_collection, len(vec_densos[0]))
        puntos = [
            PointStruct(
                id=punto_id(d.id),
                vector={VECTOR_DENSO: vd, VECTOR_DISPERSO: vs},
                payload={"id": d.id, "texto": d.texto, "fuente": d.fuente, "metadatos": d.metadatos},
            )
            for d, vd, vs in zip(documentos, vec_densos, vec_dispersos, strict=True)
        ]
        await cliente.upsert(settings.qdrant_collection, points=puntos, wait=True)
    finally:
        if propio:
            await cliente.close()
