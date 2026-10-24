"""Dobles del modo demo: repositorio en memoria, codificadores deterministas y LLM guionado.

Son copias (no importaciones) de los dobles de `tests/`: el codigo de la app no depende de
las pruebas. Ninguno hace E/S de red ni descarga modelos.
"""

import re
import zlib
from uuid import UUID, uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult
from langchain_core.runnables import RunnableLambda
from pydantic import Field
from qdrant_client.models import SparseVector

from app.domain.modelos import EntrenoRegistro, Lesion, Perfil, PerfilBorrador, Rutina

# --- Repositorio en memoria (misma interfaz que RepositorioDominio) -------------------------


class RepositorioMemoria:
    """Implementa en memoria los metodos de `app.persistencia.repositorios.RepositorioDominio`."""

    def __init__(self) -> None:
        self.usuarios: set[UUID] = set()
        self.perfiles: dict[UUID, Perfil] = {}
        self.borradores: dict[UUID, PerfilBorrador] = {}
        self.lesiones: dict[UUID, list[Lesion]] = {}
        self.rutinas: dict[UUID, list[Rutina]] = {}
        self.entrenos: dict[UUID, list[EntrenoRegistro]] = {}
        self.exclusiones: dict[UUID, list[str]] = {}

    async def crear_usuario(self) -> UUID:
        uid = uuid4()
        self.usuarios.add(uid)
        return uid

    async def guardar_perfil(self, perfil: Perfil) -> None:
        self.perfiles[perfil.usuario_id] = perfil
        self.borradores.pop(perfil.usuario_id, None)  # el perfil completo sustituye al borrador

    async def guardar_perfil_borrador(self, usuario_id: UUID, borrador: PerfilBorrador) -> None:
        self.borradores[usuario_id] = borrador

    async def obtener_perfil_borrador(self, usuario_id: UUID) -> PerfilBorrador | None:
        return self.borradores.get(usuario_id)

    async def obtener_perfil(self, usuario_id: UUID) -> Perfil | None:
        return self.perfiles.get(usuario_id)

    async def agregar_lesion(self, usuario_id: UUID, lesion: Lesion) -> None:
        self.lesiones.setdefault(usuario_id, []).append(lesion)

    async def actualizar_severidad_lesion(self, usuario_id: UUID, zona: str, severidad: str) -> None:
        self.lesiones[usuario_id] = [
            l.model_copy(update={"severidad": severidad}) if l.activa and l.zona == zona else l
            for l in self.lesiones.get(usuario_id, [])
        ]

    async def lesiones_activas(self, usuario_id: UUID) -> list[Lesion]:
        return [l for l in self.lesiones.get(usuario_id, []) if l.activa]

    async def agregar_exclusion(self, usuario_id: UUID, ejercicio_id: str) -> None:
        actuales = self.exclusiones.setdefault(usuario_id, [])
        if ejercicio_id not in actuales:
            actuales.append(ejercicio_id)

    async def exclusiones_activas(self, usuario_id: UUID) -> list[str]:
        return list(self.exclusiones.get(usuario_id, []))

    async def guardar_rutina(self, rutina: Rutina) -> None:
        previas = self.rutinas.setdefault(rutina.usuario_id, [])
        previas.append(rutina.model_copy(update={"version": len(previas) + 1}))

    async def rutina_actual(self, usuario_id: UUID) -> Rutina | None:
        previas = self.rutinas.get(usuario_id, [])
        return previas[-1] if previas else None

    async def registrar_entreno(self, entreno: EntrenoRegistro) -> None:
        self.entrenos.setdefault(entreno.usuario_id, []).append(entreno)

    async def historial(self, usuario_id: UUID, limite: int) -> list[EntrenoRegistro]:
        return list(reversed(self.entrenos.get(usuario_id, [])))[:limite]


# --- Codificadores deterministas (hashing de tokens; sin modelos) ---------------------------

_DIM = 64


def _tokens(texto: str) -> list[str]:
    return re.findall(r"\w+", texto.lower())


class DensoDeterminista:
    """Embedding denso por hashing de tokens (sustituye a sentence-transformers)."""

    def codificar(self, textos: list[str]) -> list[list[float]]:
        salida = []
        for t in textos:
            v = [0.0] * _DIM
            for tok in _tokens(t):
                v[zlib.crc32(tok.encode()) % _DIM] += 1.0
            if not any(v):
                v[0] = 1.0
            salida.append(v)
        return salida

    codificar_consulta = codificar


class DispersoDeterminista:
    """Vector disperso por conteo de tokens (sustituye a BM25 de fastembed)."""

    def codificar(self, textos: list[str]) -> list[SparseVector]:
        salida = []
        for t in textos:
            conteo: dict[int, float] = {}
            for tok in _tokens(t):
                i = zlib.crc32(tok.encode())
                conteo[i] = conteo.get(i, 0.0) + 1.0
            idx = sorted(conteo) or [0]
            salida.append(SparseVector(indices=idx, values=[conteo.get(i, 1.0) for i in idx]))
        return salida

    codificar_consulta = codificar


# --- LLM guionado -------------------------------------------------------------------------


class GuionAgotado(RuntimeError):
    """El grafo pidio una salida estructurada que el guion no tenia preparada."""


class LLMGuionado(BaseChatModel):
    """Chat model simulado: devuelve, en orden, las salidas estructuradas guionadas por esquema.

    `programar(AnalisisMensaje=[...], DecisionSupervisor=[...])` prepara el siguiente turno.
    Nunca llama a la red. Registra que esquemas pidio el grafo (`llamadas`).
    """

    guion: dict[str, list] = Field(default_factory=dict)
    llamadas: list[str] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "guionado"

    def programar(self, **salidas: list) -> None:
        for esquema, valores in salidas.items():
            self.guion.setdefault(esquema, []).extend(valores)

    def pendientes(self) -> dict[str, int]:
        return {k: len(v) for k, v in self.guion.items() if v}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        raise GuionAgotado("el modo demo solo usa salidas estructuradas")

    def with_structured_output(self, schema, **kwargs):
        nombre = schema.__name__

        def _salida(_entrada):
            self.llamadas.append(nombre)
            cola = self.guion.get(nombre) or []
            if not cola:
                raise GuionAgotado(f"el guion no tiene una salida para {nombre}")
            return cola.pop(0)

        async def _asalida(entrada):
            return _salida(entrada)

        return RunnableLambda(_salida, afunc=_asalida)
