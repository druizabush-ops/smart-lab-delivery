"""create delivery persistence tables

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "delivery_cards",
        sa.Column("card_id", sa.String(length=255), primary_key=True),
        sa.Column("patient_id", sa.String(length=255), nullable=False),
        sa.Column("lab_result_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("queue_status", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("card_id", sa.String(length=255), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["delivery_cards.card_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_delivery_attempts_card_id", "delivery_attempts", ["card_id"])


def downgrade() -> None:
    op.drop_index("ix_delivery_attempts_card_id", table_name="delivery_attempts")
    op.drop_table("delivery_attempts")
    op.drop_table("delivery_cards")
