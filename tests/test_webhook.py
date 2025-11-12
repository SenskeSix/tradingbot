import hmac
import hashlib
import json
import os
from unittest import mock

from fastapi.testclient import TestClient

os.environ.setdefault("WEBHOOK_SECRET", "testsecret")
os.environ.setdefault("DB_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_AUTH_TOKEN", "testtoken")

from app.main import app  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine, SessionLocal  # noqa: E402


Base.metadata.create_all(bind=engine)
client = TestClient(app)


def sign(body: bytes) -> str:
    return hmac.new(os.environ["WEBHOOK_SECRET"].encode(), body, hashlib.sha256).hexdigest()


def test_webhook_happy_path(monkeypatch):
    body = json.dumps(
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "symbol": "BTC-USD",
            "side": "buy",
            "price": 20000,
        }
    ).encode()

    mock_delay = mock.Mock()
    monkeypatch.setattr("app.api.routes.enqueue_trade_task", mock.Mock(delay=mock_delay))

    response = client.post("/webhook/tradingview", data=body, headers={"X-Signature": sign(body)})
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    mock_delay.assert_called_once()


def test_webhook_invalid_signature():
    body = json.dumps(
        {
            "id": "123e4567-e89b-12d3-a456-426614174111",
            "symbol": "BTC-USD",
            "side": "buy",
            "price": 20000,
        }
    ).encode()
    response = client.post("/webhook/tradingview", data=body, headers={"X-Signature": "bad"})
    assert response.status_code == 401


def test_webhook_duplicate_alert(monkeypatch):
    body = json.dumps(
        {
            "id": "123e4567-e89b-12d3-a456-426614174222",
            "symbol": "BTC-USD",
            "side": "buy",
            "price": 20000,
        }
    ).encode()
    mock_delay = mock.Mock()
    monkeypatch.setattr("app.api.routes.enqueue_trade_task", mock.Mock(delay=mock_delay))

    response = client.post("/webhook/tradingview", data=body, headers={"X-Signature": sign(body)})
    assert response.status_code == 200

    response2 = client.post("/webhook/tradingview", data=body, headers={"X-Signature": sign(body)})
    assert response2.json()["status"] == "duplicate"
