import os
from unittest import mock

os.environ.setdefault("WEBHOOK_SECRET", "test")
os.environ.setdefault("DB_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_AUTH_TOKEN", "testtoken")
os.environ.setdefault("COINBASE_API_SECRET", "abc")
os.environ.setdefault("COINBASE_API_KEY", "abc")
os.environ.setdefault("COINBASE_API_PASSPHRASE", "pass")

from app.services.coinbase import CoinbaseClient  # noqa: E402


def test_place_order(monkeypatch):
    client = CoinbaseClient()
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"order_id": "1"}

    def fake_request(method, url, headers=None, json=None):  # noqa: ANN001
        return mock_response

    monkeypatch.setattr(client.client, "request", fake_request)
    resp = client.place_order("BTC-USD", "BUY", 0.1, 20000)
    assert resp["order_id"] == "1"
