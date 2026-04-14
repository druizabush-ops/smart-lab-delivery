"""add operator action audit table

Revision ID: 20260414_0002
Revises: 20260413_0001
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operator_action_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("command", sa.String(length=64), nullable=False),
        sa.Column("card_id", sa.String(length=255), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_operator_action_log_card_id", "operator_action_log", ["card_id"])


def downgrade() -> None:
    op.drop_index("ix_operator_action_log_card_id", table_name="operator_action_log")
    op.drop_table("operator_action_log")
