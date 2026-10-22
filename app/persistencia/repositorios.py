from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.domain.modelos import DiaRutina, EntrenoRegistro, Lesion, Nivel, Perfil, Rutina
from app.persistencia.tablas import (
    EntrenoTabla, LesionTabla, PerfilTabla, RutinaTabla, UsuarioTabla,
)


def crear_motor(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True)


async def _asegurar_usuario(s: AsyncSession, usuario_id: UUID) -> None:
    await s.execute(
        pg_insert(UsuarioTabla).values(id=usuario_id).on_conflict_do_nothing(index_elements=["id"])
    )


class RepositorioDominio:
    def __init__(self, sesion_factory: async_sessionmaker):
        self._sesion_factory = sesion_factory

    async def crear_usuario(self) -> UUID:
        async with self._sesion_factory() as s, s.begin():
            res = await s.execute(
                pg_insert(UsuarioTabla).values(id=uuid4()).returning(UsuarioTabla.id)
            )
            return res.scalar_one()

    async def guardar_perfil(self, perfil: Perfil) -> None:
        valores = dict(
            objetivo=perfil.objetivo,
            dias_disponibles=perfil.dias_disponibles,
            equipo=list(perfil.equipo),
            nivel=perfil.nivel.value,
        )
        async with self._sesion_factory() as s, s.begin():
            await _asegurar_usuario(s, perfil.usuario_id)
            stmt = pg_insert(PerfilTabla).values(usuario_id=perfil.usuario_id, **valores)
            await s.execute(
                stmt.on_conflict_do_update(
                    index_elements=["usuario_id"], set_={**valores, "actualizado_en": func.now()}
                )
            )

    async def obtener_perfil(self, usuario_id: UUID) -> Perfil | None:
        async with self._sesion_factory() as s:
            fila = await s.get(PerfilTabla, usuario_id)
            if fila is None:
                return None
            return Perfil(
                usuario_id=fila.usuario_id,
                objetivo=fila.objetivo,
                dias_disponibles=fila.dias_disponibles,
                equipo=list(fila.equipo),
                nivel=Nivel(fila.nivel),
            )

    async def agregar_lesion(self, usuario_id: UUID, lesion: Lesion) -> None:
        async with self._sesion_factory() as s, s.begin():
            await _asegurar_usuario(s, usuario_id)
            s.add(LesionTabla(
                usuario_id=usuario_id, zona=lesion.zona,
                severidad=lesion.severidad, activa=lesion.activa,
            ))

    async def lesiones_activas(self, usuario_id: UUID) -> list[Lesion]:
        async with self._sesion_factory() as s:
            res = await s.scalars(
                select(LesionTabla)
                .where(LesionTabla.usuario_id == usuario_id, LesionTabla.activa.is_(True))
                .order_by(LesionTabla.registrada_en, LesionTabla.id)
            )
            return [Lesion(zona=f.zona, severidad=f.severidad, activa=f.activa) for f in res]

    async def guardar_rutina(self, rutina: Rutina) -> None:
        """Guarda una nueva version; la version la asigna el repositorio."""
        contenido = [d.model_dump(mode="json") for d in rutina.dias]
        async with self._sesion_factory() as s, s.begin():
            await _asegurar_usuario(s, rutina.usuario_id)
            # Bloquea la fila del usuario para serializar altas de version concurrentes.
            await s.execute(
                select(UsuarioTabla.id).where(UsuarioTabla.id == rutina.usuario_id).with_for_update()
            )
            maxima = await s.scalar(
                select(func.max(RutinaTabla.version)).where(RutinaTabla.usuario_id == rutina.usuario_id)
            )
            s.add(RutinaTabla(
                usuario_id=rutina.usuario_id, version=(maxima or 0) + 1, contenido=contenido,
            ))

    async def rutina_actual(self, usuario_id: UUID) -> Rutina | None:
        async with self._sesion_factory() as s:
            fila = await s.scalar(
                select(RutinaTabla)
                .where(RutinaTabla.usuario_id == usuario_id)
                .order_by(RutinaTabla.version.desc())
                .limit(1)
            )
            if fila is None:
                return None
            return Rutina(
                usuario_id=fila.usuario_id,
                version=fila.version,
                dias=[DiaRutina.model_validate(d) for d in fila.contenido],
            )

    async def registrar_entreno(self, entreno: EntrenoRegistro) -> None:
        async with self._sesion_factory() as s, s.begin():
            await _asegurar_usuario(s, entreno.usuario_id)
            s.add(EntrenoTabla(**entreno.model_dump()))

    async def historial(self, usuario_id: UUID, limite: int) -> list[EntrenoRegistro]:
        async with self._sesion_factory() as s:
            res = await s.scalars(
                select(EntrenoTabla)
                .where(EntrenoTabla.usuario_id == usuario_id)
                .order_by(EntrenoTabla.fecha.desc(), EntrenoTabla.id.desc())
                .limit(limite)
            )
            return [
                EntrenoRegistro(
                    usuario_id=f.usuario_id, fecha=f.fecha, ejercicio_id=f.ejercicio_id,
                    series=f.series, repeticiones=f.repeticiones, peso_kg=f.peso_kg,
                    rpe=f.rpe, notas=f.notas,
                )
                for f in res
            ]
