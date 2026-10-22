import uuid

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
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
    disperso_por_defecto,
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


async def asegurar_coleccion(cliente: AsyncQdrantClient, nombre: str, dim: int) -> None:
    """Crea la coleccion (vector denso + disperso) solo si no existe."""
    if not await cliente.collection_exists(nombre):
        try:
            await cliente.create_collection(
                nombre,
                vectors_config={VECTOR_DENSO: VectorParams(size=dim, distance=Distance.COSINE)},
                sparse_vectors_config={VECTOR_DISPERSO: SparseVectorParams()},
            )
        except Exception:
            # carrera con otro proceso: si ya existe, es exito
            if not await cliente.collection_exists(nombre):
                raise
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
    disperso = disperso or disperso_por_defecto()
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
