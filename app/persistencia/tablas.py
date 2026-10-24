from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UsuarioTabla(Base):
    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PerfilTabla(Base):
    __tablename__ = "perfiles"

    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    objetivo: Mapped[str] = mapped_column(Text, nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False)
    equipo: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PerfilBorradorTabla(Base):
    """Perfil parcial mientras el onboarding no se completa (columnas nulas). Dato de dominio:
    sobrevive a reinicios y a un hilo reiniciado; se borra al guardar el perfil completo."""

    __tablename__ = "perfiles_borrador"

    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    dias_disponibles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipo: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    nivel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LesionTabla(Base):
    __tablename__ = "lesiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    zona: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False)
    registrada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RutinaTabla(Base):
    __tablename__ = "rutinas"
    __table_args__ = (
        UniqueConstraint("usuario_id", "version", name="uq_rutinas_usuario_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    contenido: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EntrenoTabla(Base):
    __tablename__ = "entrenos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # id del catalogo de ejercicios (no hay tabla de catalogo)
    ejercicio_id: Mapped[str] = mapped_column(String(100), nullable=False)
    series: Mapped[int] = mapped_column(Integer, nullable=False)
    repeticiones: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_kg: Mapped[float] = mapped_column(Float, nullable=False)
    rpe: Mapped[int] = mapped_column(Integer, nullable=False)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExclusionDolorTabla(Base):
    """Ejercicio excluido por dolor agudo: dato de dominio (como las lesiones), no del hilo."""

    __tablename__ = "exclusiones_dolor"
    __table_args__ = (
        UniqueConstraint("usuario_id", "ejercicio_id", name="uq_exclusiones_dolor_usuario_ejercicio"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    ejercicio_id: Mapped[str] = mapped_column(String(100), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
