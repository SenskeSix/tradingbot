from __future__ import annotations

import uuid

from celery import Celery

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.trading import TradingService

settings = get_settings()

celery_app = Celery(
    "tradingbot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_routes = {"enqueue_trade_task": {"queue": "trades"}}


@celery_app.task(name="enqueue_trade_task")
def enqueue_trade_task(alert_id: str) -> str:
    session = SessionLocal()
    try:
        service = TradingService(session, settings)
        service.execute_alert(uuid.UUID(alert_id))
        return alert_id
    finally:
        session.close()
