"""Codificadores denso y disperso, inyectables mediante Protocol."""
import asyncio
from typing import Protocol

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import SparseVector

from app.settings import Settings

VECTOR_DENSO = "denso"
VECTOR_DISPERSO = "disperso"
MODELO_BM25 = "Qdrant/bm25"


class CodificadorDenso(Protocol):
    def codificar(self, textos: list[str]) -> list[list[float]]: ...
    def codificar_consulta(self, textos: list[str]) -> list[list[float]]: ...


class CodificadorDisperso(Protocol):
    def codificar(self, textos: list[str]) -> list[SparseVector]: ...
    def codificar_consulta(self, textos: list[str]) -> list[SparseVector]: ...


class DensoSentenceTransformers:
    """Modelo de sentence-transformers tomado de Settings.embedding_model (carga perezosa)."""

    def __init__(self, nombre_modelo: str):
        self._nombre = nombre_modelo
        self._modelo = None

    def codificar(self, textos: list[str]) -> list[list[float]]:
        if self._modelo is None:
            from sentence_transformers import SentenceTransformer

            self._modelo = SentenceTransformer(self._nombre)
        return self._modelo.encode(textos, normalize_embeddings=True).tolist()

    codificar_consulta = codificar


class DispersoBM25:
    """BM25 disperso via fastembed (carga perezosa)."""

    def __init__(self):
        self._modelo = None

    def _cargar(self):
        if self._modelo is None:
            from fastembed import SparseTextEmbedding

            self._modelo = SparseTextEmbedding(MODELO_BM25)
        return self._modelo

    @staticmethod
    def _a_vector(e) -> SparseVector:
        return SparseVector(indices=e.indices.tolist(), values=e.values.tolist())

    def codificar(self, textos: list[str]) -> list[SparseVector]:
        return [self._a_vector(e) for e in self._cargar().passage_embed(textos)]

    def codificar_consulta(self, textos: list[str]) -> list[SparseVector]:
        return [self._a_vector(e) for e in self._cargar().query_embed(textos)]


_denso_por_defecto: dict[str, DensoSentenceTransformers] = {}
_disperso_por_defecto = DispersoBM25()


def denso_desde_settings(settings: Settings) -> CodificadorDenso:
    # cache por nombre de modelo: evita recargar pesos en cada llamada
    return _denso_por_defecto.setdefault(
        settings.embedding_model, DensoSentenceTransformers(settings.embedding_model)
    )


def disperso_por_defecto() -> CodificadorDisperso:
    return _disperso_por_defecto


def cliente_desde_settings(settings: Settings) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.qdrant_url)


async def en_hilo(funcion, textos: list[str]):
    """Ejecuta un codificador (CPU/bloqueante) fuera del event loop."""
    return await asyncio.to_thread(funcion, textos)
