from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, Fusion, FusionQuery, MatchValue, Prefetch

from app.domain.modelos import Nivel
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
from app.rag.ingesta import Documento
from app.settings import Settings


class FiltrosBusqueda(BaseModel):
    equipo: str | None = None
    nivel: Nivel | None = None
    musculo: str | None = None


def _filtro_payload(f: FiltrosBusqueda) -> Filter | None:
    valores = {
        "equipo": f.equipo,
        "nivel": f.nivel.value if f.nivel else None,
        "musculo": f.musculo,
    }
    must = [
        FieldCondition(key=f"metadatos.{k}", match=MatchValue(value=v))
        for k, v in valores.items()
        if v is not None
    ]
    return Filter(must=must) if must else None


async def buscar(
    consulta: str,
    filtros: FiltrosBusqueda,
    k: int,
    settings: Settings,
    *,
    cliente: AsyncQdrantClient | None = None,
    denso: CodificadorDenso | None = None,
    disperso: CodificadorDisperso | None = None,
) -> list[Documento]:
    propio = cliente is None
    cliente = cliente or cliente_desde_settings(settings)
    denso = denso or denso_desde_settings(settings)
    disperso = disperso or disperso_desde_settings(settings)
    try:
        vd = (await en_hilo(denso.codificar_consulta, [consulta]))[0]
        vs = (await en_hilo(disperso.codificar_consulta, [consulta]))[0]
        filtro = _filtro_payload(filtros)
        # el filtro va en cada prefetch (filtrado previo a cada ranking) y la fusion RRF es del servidor
        previos = max(k * 4, 20)
        resp = await cliente.query_points(
            settings.qdrant_collection,
            prefetch=[
                Prefetch(query=vd, using=VECTOR_DENSO, filter=filtro, limit=previos),
                Prefetch(query=vs, using=VECTOR_DISPERSO, filter=filtro, limit=previos),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            query_filter=filtro,
            limit=k,
            with_payload=True,
        )
    finally:
        if propio:
            await cliente.close()
    return [
        Documento(
            id=p.payload["id"],
            texto=p.payload["texto"],
            fuente=p.payload["fuente"],
            metadatos=p.payload["metadatos"],
        )
        for p in resp.points
    ]
