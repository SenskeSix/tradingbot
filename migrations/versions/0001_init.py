from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Numeric(18, 8), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("timeframe", sa.String(length=20)),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("limit_price", sa.Numeric(18, 8), nullable=False),
        sa.Column("status", sa.String(length=20)),
        sa.Column("mode", sa.String(length=10)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "fills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("price", sa.Numeric(18, 8), nullable=False),
        sa.Column("fee", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("filled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "positions",
        sa.Column("symbol", sa.String(length=50), primary_key=True),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "risk_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "daily_risk",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trade_day", sa.String(length=10), nullable=False, unique=True),
        sa.Column("notional_used", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("daily_risk")
    op.drop_table("risk_events")
    op.drop_table("positions")
    op.drop_table("fills")
    op.drop_table("orders")
    op.drop_table("alerts")
