import os

os.environ.setdefault("WEBHOOK_SECRET", "test")
os.environ.setdefault("DB_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_AUTH_TOKEN", "testtoken")

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402
from app.db import models  # noqa: E402
from app.services.risk import RiskEngine  # noqa: E402

Base.metadata.create_all(bind=engine)


def test_position_limit_block():
    session = SessionLocal()
    try:
        settings = get_settings()
        engine_risk = RiskEngine(session, settings)
        result = engine_risk.check_position_limits("BTC-USD", proposed_qty=10, price=10000, side="buy")
        assert not result.ok
    finally:
        session.close()
