from __future__ import annotations

import base64
import hmac
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings, get_settings

COINBASE_API_URL = "https://api.coinbase.com/api/v3"


class CoinbaseError(Exception):
    pass


class CoinbaseRateLimitError(CoinbaseError):
    pass


@dataclass
class BidAsk:
    best_bid: float
    best_ask: float


class CoinbaseClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = httpx.Client(timeout=10)

    def _signed_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        timestamp = str(int(time.time()))
        message = f"{timestamp}{method.upper()}{path}{body}"
        secret = self.settings.coinbase_api_secret or ""
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        encoded = base64.b64encode(signature).decode()
        return {
            "CB-ACCESS-KEY": self.settings.coinbase_api_key or "",
            "CB-ACCESS-SIGN": encoded,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": self.settings.coinbase_api_passphrase or "",
            "Content-Type": "application/json",
        }

    def _request(
        self, method: str, path: str, json_body: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        body_str = json.dumps(json_body) if json_body else ""
        headers = self._signed_headers(method, path, body_str)
        response = self.client.request(
            method, f"{COINBASE_API_URL}{path}", headers=headers, json=json_body
        )
        if response.status_code == 429:
            raise CoinbaseRateLimitError("rate limited")
        response.raise_for_status()
        return response.json()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=4), stop=stop_after_attempt(3))
    def get_accounts(self) -> Dict[str, Any]:
        return self._request("GET", "/brokerage/accounts")

    @retry(wait=wait_exponential(multiplier=1, min=1, max=4), stop=stop_after_attempt(3))
    def get_best_bid_ask(self, symbol: str) -> BidAsk:
        data = self._request("GET", f"/brokerage/products/{symbol}")
        price = data.get("price") or {}
        return BidAsk(
            best_bid=float(price.get("best_bid", 0)), best_ask=float(price.get("best_ask", 0))
        )

    @retry(wait=wait_exponential(multiplier=1, min=1, max=4), stop=stop_after_attempt(3))
    def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        limit_price: float,
        time_in_force: str = "IOC",
    ) -> Dict[str, Any]:
        side = side.upper()
        payload = {
            "client_order_id": str(time.time_ns()),
            "product_id": symbol,
            "side": side,
            "order_configuration": {
                "limit_limit_gtc": {
                    "base_size": str(size),
                    "limit_price": str(limit_price),
                    "post_only": False,
                }
            },
        }
        return self._request("POST", "/brokerage/orders", payload)

    def get_fills(self, order_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/brokerage/orders/{order_id}")


def get_coinbase_client() -> CoinbaseClient:
    return CoinbaseClient()
