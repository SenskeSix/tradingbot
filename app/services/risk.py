from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import models


@dataclass
class RiskResult:
    ok: bool
    reason: str | None = None


class RiskEngine:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def _portfolio_notional(self) -> float:
        # In paper mode we use configured cash; in live mode we assume same for now
        return float(self.settings.paper_cash_usd)

    def check_position_limits(
        self, symbol: str, proposed_qty: float, price: float, side: str
    ) -> RiskResult:
        limit = self._portfolio_notional() * self.settings.max_pos_pct
        stmt = select(models.Position).where(models.Position.symbol == symbol)
        position = self.db.execute(stmt).scalar_one_or_none()
        current_qty = float(position.qty) if position else 0.0
        delta_qty = proposed_qty if side == "buy" else -proposed_qty
        projected_qty = current_qty + delta_qty
        projected_notional = abs(projected_qty * price)
        if projected_notional > limit:
            return RiskResult(False, "position limit exceeded")
        return RiskResult(True)

    def check_daily_risk(self, proposed_notional: float) -> RiskResult:
        today = dt.datetime.utcnow().date().isoformat()
        stmt = select(models.DailyRisk).where(models.DailyRisk.trade_day == today)
        record = self.db.execute(stmt).scalar_one_or_none()
        limit = self._portfolio_notional() * self.settings.max_daily_risk_pct
        current = float(record.notional_used) if record else 0.0
        if current + proposed_notional > limit:
            return RiskResult(False, "daily risk limit exceeded")
        if record:
            record.notional_used = current + proposed_notional
        else:
            record = models.DailyRisk(trade_day=today, notional_used=proposed_notional)
            self.db.add(record)
        self.db.commit()
        return RiskResult(True)

    def check_slippage(self, alert_price: float, market_price: float) -> RiskResult:
        deviation = abs(market_price - alert_price) / alert_price if alert_price else 0
        if deviation > self.settings.order_slippage_pct:
            return RiskResult(False, "slippage too high")
        return RiskResult(True)

    def record_risk_event(self, event_type: str, details: dict) -> None:
        event = models.RiskEvent(type=event_type, details=details)
        self.db.add(event)
        self.db.commit()
