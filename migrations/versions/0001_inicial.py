"""inicial

Revision ID: 0001
Revises:
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "perfiles",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objetivo", sa.Text(), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False),
        sa.Column("equipo", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("nivel", sa.String(length=20), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("usuario_id"),
    )
    op.create_table(
        "lesiones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("zona", sa.Text(), nullable=False),
        sa.Column("severidad", sa.String(length=20), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("registrada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesiones_usuario_id", "lesiones", ["usuario_id"])
    op.create_table(
        "rutinas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("contenido", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "version", name="uq_rutinas_usuario_version"),
    )
    op.create_table(
        "entrenos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("ejercicio_id", sa.String(length=100), nullable=False),
        sa.Column("series", sa.Integer(), nullable=False),
        sa.Column("repeticiones", sa.Integer(), nullable=False),
        sa.Column("peso_kg", sa.Float(), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entrenos_usuario_id", "entrenos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_entrenos_usuario_id", table_name="entrenos")
    op.drop_table("entrenos")
    op.drop_table("rutinas")
    op.drop_index("ix_lesiones_usuario_id", table_name="lesiones")
    op.drop_table("lesiones")
    op.drop_table("perfiles")
    op.drop_table("usuarios")
