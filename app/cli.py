from __future__ import annotations

import argparse
import datetime as dt

from sqlalchemy import func

from app.config import get_settings
from app.db.session import SessionLocal
from app.db import models
from app.services.reporting import daily_pnl_report


def seed_demo() -> None:
    settings = get_settings()
    session = SessionLocal()
    try:
        for symbol in settings.base_assets:
            if not session.get(models.Position, symbol):
                session.add(models.Position(symbol=symbol, qty=0, avg_price=0))
        session.commit()
        print("Seeded demo positions for", ", ".join(settings.base_assets))
    finally:
        session.close()


def report(day: str | None) -> None:
    session = SessionLocal()
    try:
        day = day or dt.datetime.utcnow().date().isoformat()
        target_date = dt.datetime.fromisoformat(day).date()
        report_rows = daily_pnl_report(session, target_date)
        for row in report_rows:
            print(
                f"{row['date']} {row['symbol']}: realized={row['realized_pnl']} unrealized={row['unrealized_pnl']}"
            )
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="TradingBot CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("seed-demo")

    report_parser = sub.add_parser("report")
    report_parser.add_argument("--day", dest="day", help="YYYY-MM-DD", default=None)

    args = parser.parse_args()
    if args.command == "seed-demo":
        seed_demo()
    elif args.command == "report":
        report(args.day)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
