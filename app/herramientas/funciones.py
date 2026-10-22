"""Herramientas de los agentes.

Todas van decoradas con `pydantic.validate_call(validate_return=True)`: las entradas y la salida
se validan en tiempo de ejecucion (tambien en las funciones async: la salida se valida al
esperar la corrutina). Un argumento mal tipado lanza `pydantic.ValidationError`.
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import ConfigDict, Field, validate_call

from app.domain.modelos import Ejercicio, EntrenoRegistro, Lesion, Rutina
from app.herramientas.esquemas import EntradaVolumen, SalidaVolumen
from app.rag.ingesta import Documento
from app.rag.recuperador import FiltrosBusqueda, buscar
from app.safety.reglas import IndiceBloqueo, filtrar_por_lesiones
from app.settings import Settings, get_settings

# Tipos que no son modelos Pydantic (repositorio, indice) se comprueban con isinstance.
_CONFIG = ConfigDict(arbitrary_types_allowed=True)
_validar = validate_call(config=_CONFIG, validate_return=True)


@runtime_checkable
class RepoHistorial(Protocol):
    """Lo unico que `consultar_historial` necesita del repositorio."""

    async def historial(self, usuario_id: UUID, limite: int) -> list[EntrenoRegistro]: ...


class EjercicioDesconocido(Exception):
    """Un ejercicio de la rutina no existe en el catalogo."""


@_validar
def volumen_semanal(entrada: EntradaVolumen) -> SalidaVolumen:
    """Suma las series de la rutina por musculo.

    Solo cuenta las series para `musculo_primario`; los secundarios no suman.
    Lanza EjercicioDesconocido si un ejercicio de la rutina no esta en el catalogo.
    """
    series: dict[str, int] = {}
    for dia in entrada.rutina.dias:
        for plan in dia.ejercicios:
            ej = entrada.catalogo.get(plan.ejercicio_id)
            if ej is None:
                raise EjercicioDesconocido(f"Ejercicio fuera del catalogo: {plan.ejercicio_id!r}")
            series[ej.musculo_primario] = series.get(ej.musculo_primario, 0) + plan.series
    return SalidaVolumen(series_por_musculo=series)


@_validar
async def consultar_historial(
    repo: RepoHistorial, usuario_id: UUID, limite: int = Field(ge=1)
) -> list[EntrenoRegistro]:
    return await repo.historial(usuario_id, limite)


@_validar
async def validar_plan(
    rutina: Rutina,
    lesiones: list[Lesion],
    catalogo: dict[str, Ejercicio],
    indice: IndiceBloqueo | None = None,
) -> list[str]:
    """Devuelve los ejercicio_id bloqueados (vacio si el plan es seguro).

    Falla cerrado: un id ausente del catalogo no se puede verificar y se devuelve como
    bloqueado. ZonaLesionDesconocida se propaga sin capturar. Orden de primera aparicion.
    Con `indice` (precalculado sobre el catalogo) la comprobacion son busquedas en conjuntos.
    """
    ids = list(dict.fromkeys(p.ejercicio_id for d in rutina.dias for p in d.ejercicios))
    conocidos = [catalogo[i] for i in ids if i in catalogo]
    bloqueados = {i for i, _zona in filtrar_por_lesiones(conocidos, lesiones, indice).bloqueados}
    return [i for i in ids if i in bloqueados or i not in catalogo]


@_validar
async def buscar_conocimiento(
    consulta: str,
    filtros: FiltrosBusqueda,
    *,
    k: int = Field(default=5, ge=1),
    settings: Settings | None = None,
) -> list[Documento]:
    return await buscar(consulta, filtros, k, settings or get_settings())
