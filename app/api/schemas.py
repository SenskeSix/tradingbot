from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlertIn(BaseModel):
    id: UUID = Field(..., description="TradingView alert id")
    symbol: str
    side: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    timeframe: str | None = None
    price: float
    ts: datetime | None = None


class AlertResponse(BaseModel):
    status: str
    alert_id: UUID


class HealthResponse(BaseModel):
    status: str
    build_sha: str
    db: str
    redis: str


class ReportResponse(BaseModel):
    symbol: str
    date: str
    realized_pnl: float
    unrealized_pnl: float
