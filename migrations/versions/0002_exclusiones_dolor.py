"""exclusiones por dolor agudo como dato de dominio

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exclusiones_dolor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ejercicio_id", sa.String(length=100), nullable=False),
        sa.Column("activa", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "ejercicio_id", name="uq_exclusiones_dolor_usuario_ejercicio"),
    )
    op.create_index("ix_exclusiones_dolor_usuario_id", "exclusiones_dolor", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_exclusiones_dolor_usuario_id", table_name="exclusiones_dolor")
    op.drop_table("exclusiones_dolor")
