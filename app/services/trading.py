from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import models
from app.metrics import orders_filled, orders_sent, risk_blocked, trade_latency
from app.services import marketdata, sizing
from app.services.coinbase import CoinbaseClient
from app.services.idempotency import throttle_symbol
from app.services.risk import RiskEngine

logger = logging.getLogger(__name__)


class TradingService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.risk = RiskEngine(db, settings)
        self.coinbase_client = CoinbaseClient(settings)
        self.marketdata = marketdata.MarketDataService(self.coinbase_client, settings)

    def _load_alert(self, alert_id: uuid.UUID) -> models.Alert | None:
        stmt = select(models.Alert).where(models.Alert.id == alert_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def execute_alert(self, alert_id: uuid.UUID) -> None:
        alert = self._load_alert(alert_id)
        if not alert:
            logger.warning("alert missing", extra={"alert_id": str(alert_id)})
            return

        side = (alert.side or "").lower()
        if side == "flat":
            self.risk.record_risk_event("flat", {"alert_id": str(alert.id)})
            return
        if side not in {"buy", "sell"}:
            self._risk_block(alert, "invalid_side")
            return

        if not throttle_symbol(alert.symbol, self.settings.throttle_seconds):
            self._risk_block(alert, "throttled")
            return

        with trade_latency.time():
            alert_price = float(alert.price)
            market_price = self.marketdata.get_mid_price(alert.symbol, fallback=alert_price)
            cash = float(self.settings.paper_cash_usd)
            qty, sizing_mode = sizing.position_size_vol_scaled(
                market_price, None, self.settings.max_pos_pct, cash
            )
            if qty <= 0:
                self._risk_block(alert, "qty<=0")
                return

            notional = qty * market_price
            checks = [
                self.risk.check_slippage(alert_price, market_price),
                self.risk.check_position_limits(alert.symbol, qty, market_price, side),
                self.risk.check_daily_risk(notional),
            ]
            for check in checks:
                if not check.ok:
                    self._risk_block(alert, check.reason or "risk_failed")
                    return

            direction = 1 if side == "buy" else -1
            slippage_factor = self.settings.order_slippage_pct
            limit_price = market_price * (1 + direction * slippage_factor)

            if self.settings.trading_mode == "paper":
                self._paper_fill(alert, qty, limit_price, market_price, sizing_mode, side)
            else:
                self._live_order(alert, qty, limit_price, sizing_mode, side)

    def _paper_fill(
        self,
        alert: models.Alert,
        qty: float,
        limit_price: float,
        fill_price: float,
        sizing_mode: str,
        side: str,
    ) -> None:
        order = models.Order(
            alert_id=alert.id,
            symbol=alert.symbol,
            side=side,
            qty=qty,
            limit_price=limit_price,
            status="filled",
            mode="paper",
        )
        self.db.add(order)
        self.db.flush()
        orders_sent.inc()
        fill = models.Fill(order_id=order.id, symbol=alert.symbol, qty=qty, price=fill_price, fee=0)
        self.db.add(fill)

        position = self.db.get(models.Position, alert.symbol)
        if not position:
            position = models.Position(symbol=alert.symbol, qty=0, avg_price=0)
            self.db.add(position)
        if side == "buy":
            total_qty = float(position.qty) + qty
            position.avg_price = (
                (float(position.qty) * float(position.avg_price) + qty * fill_price) / total_qty
                if total_qty
                else fill_price
            )
            position.qty = total_qty
        else:
            position.qty = float(position.qty) - qty
        self.db.commit()
        orders_filled.inc()
        self.risk.record_risk_event(
            "paper_fill",
            {"symbol": alert.symbol, "qty": qty, "side": side, "sizing": sizing_mode},
        )

    def _live_order(
        self, alert: models.Alert, qty: float, limit_price: float, sizing_mode: str, side: str
    ) -> None:
        response = self.coinbase_client.place_order(alert.symbol, side, qty, limit_price)
        order = models.Order(
            alert_id=alert.id,
            symbol=alert.symbol,
            side=side,
            qty=qty,
            limit_price=limit_price,
            status="submitted",
            mode="live",
        )
        self.db.add(order)
        self.db.commit()
        orders_sent.inc()
        self.risk.record_risk_event(
            "live_order",
            {
                "symbol": alert.symbol,
                "qty": qty,
                "side": side,
                "resp": response,
                "sizing": sizing_mode,
            },
        )

    def _risk_block(self, alert: models.Alert, reason: str) -> None:
        risk_blocked.inc()
        self.risk.record_risk_event("blocked", {"reason": reason, "alert_id": str(alert.id)})
