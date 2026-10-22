from uuid import UUID

from app.domain.modelos import Ejercicio, EntrenoRegistro, Lesion, Rutina
from app.herramientas.esquemas import EntradaVolumen, SalidaVolumen
from app.persistencia.repositorios import RepositorioDominio
from app.rag.ingesta import Documento
from app.rag.recuperador import FiltrosBusqueda, buscar
from app.safety.reglas import filtrar_por_lesiones
from app.settings import Settings, get_settings


class EjercicioDesconocido(Exception):
    """Un ejercicio de la rutina no existe en el catalogo."""


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


async def consultar_historial(
    repo: RepositorioDominio, usuario_id: UUID, limite: int
) -> list[EntrenoRegistro]:
    return await repo.historial(usuario_id, limite)


async def validar_plan(
    rutina: Rutina, lesiones: list[Lesion], catalogo: dict[str, Ejercicio]
) -> list[str]:
    """Devuelve los ejercicio_id bloqueados (vacio si el plan es seguro).

    Falla cerrado: un id ausente del catalogo no se puede verificar y se devuelve como
    bloqueado. ZonaLesionDesconocida se propaga sin capturar. Orden de primera aparicion.
    """
    ids = list(dict.fromkeys(p.ejercicio_id for d in rutina.dias for p in d.ejercicios))
    conocidos = [catalogo[i] for i in ids if i in catalogo]
    bloqueados = {i for i, _zona in filtrar_por_lesiones(conocidos, lesiones).bloqueados}
    return [i for i in ids if i in bloqueados or i not in catalogo]


async def buscar_conocimiento(
    consulta: str,
    filtros: FiltrosBusqueda,
    *,
    k: int = 5,
    settings: Settings | None = None,
) -> list[Documento]:
    return await buscar(consulta, filtros, k, settings or get_settings())
