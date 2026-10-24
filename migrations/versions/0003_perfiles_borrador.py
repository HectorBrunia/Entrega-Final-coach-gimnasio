"""perfil parcial del onboarding (borrador) como dato de dominio

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfiles_borrador",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("dias_disponibles", sa.Integer(), nullable=True),
        sa.Column("equipo", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("nivel", sa.String(length=20), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("usuario_id"),
    )


def downgrade() -> None:
    op.drop_table("perfiles_borrador")
