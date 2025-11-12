from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models


def daily_pnl_report(db: Session, target_date: dt.date) -> List[dict]:
    realized = defaultdict(float)
    last_price = {}
    fills = (
        db.query(models.Fill, models.Order)
        .join(models.Order, models.Fill.order_id == models.Order.id)
        .filter(func.date(models.Fill.filled_at) == target_date)
        .all()
    )
    for fill, order in fills:
        qty = float(fill.qty)
        price = float(fill.price)
        side = order.side
        direction = 1 if side == "sell" else -1
        realized[fill.symbol] += direction * qty * price
        last_price[fill.symbol] = price

    positions = db.query(models.Position).all()
    report = []
    handled = set()
    for position in positions:
        symbol = position.symbol
        qty = float(position.qty)
        avg_price = float(position.avg_price)
        market_price = last_price.get(symbol, avg_price)
        unrealized = qty * (market_price - avg_price)
        report.append(
            {
                "symbol": symbol,
                "date": target_date.isoformat(),
                "realized_pnl": round(realized.get(symbol, 0.0), 2),
                "unrealized_pnl": round(unrealized, 2),
            }
        )
        handled.add(symbol)
    for symbol, realized_value in realized.items():
        if symbol in handled:
            continue
        report.append(
            {
                "symbol": symbol,
                "date": target_date.isoformat(),
                "realized_pnl": round(realized_value, 2),
                "unrealized_pnl": 0.0,
            }
        )
    return report
