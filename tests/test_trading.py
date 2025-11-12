import os
import uuid
import datetime as dt

os.environ.setdefault("WEBHOOK_SECRET", "test")
os.environ.setdefault("DB_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_AUTH_TOKEN", "testtoken")

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
from app.db import models  # noqa: E402
from app.services.trading import TradingService  # noqa: E402
from app.services.reporting import daily_pnl_report  # noqa: E402

Base.metadata.create_all(bind=engine)


def test_paper_trade_updates_position(monkeypatch):
    session = SessionLocal()
    settings = get_settings()
    alert_id = uuid.uuid4()
    session.add(
        models.Alert(
            id=alert_id,
            symbol="BTC-USD",
            side="buy",
            price=20000,
        )
    )
    session.commit()

    service = TradingService(session, settings)
    monkeypatch.setattr(service.marketdata, "get_mid_price", lambda symbol: 20000)
    service.execute_alert(alert_id)

    position = session.get(models.Position, "BTC-USD")
    assert position is not None
    assert float(position.qty) > 0
    report = daily_pnl_report(session, dt.datetime.utcnow().date())
    assert report
    session.close()
