import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(20))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="alert")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    limit_price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    mode: Mapped[str] = mapped_column(String(10), default="paper")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alert: Mapped[Alert] = relationship(back_populates="orders", foreign_keys=[alert_id])
    fills: Mapped[list["Fill"]] = relationship(back_populates="order")


class Fill(Base):
    __tablename__ = "fills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    order: Mapped[Order] = relationship(back_populates="fills", foreign_keys=[order_id])


class Position(Base):
    __tablename__ = "positions"

    symbol: Mapped[str] = mapped_column(String(50), primary_key=True)
    qty: Mapped[float] = mapped_column(Numeric(24, 8), default=0)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DailyRisk(Base):
    __tablename__ = "daily_risk"
    __table_args__ = (UniqueConstraint("trade_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_day: Mapped[str] = mapped_column(String(10), nullable=False)
    notional_used: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
