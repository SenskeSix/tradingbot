#!/usr/bin/env python
"""Send dummy TradingView-like alerts for paper trading."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import random
import time
import uuid

import httpx


def build_alert(symbol: str, side: str, price: float) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "side": side,
        "confidence": round(random.uniform(0.4, 0.95), 2),
        "timeframe": "1h",
        "price": price,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send paper trading mock alerts")
    parser.add_argument("--count", type=int, default=3, help="number of alerts to send")
    parser.add_argument("--delay", type=float, default=2.0, help="delay between alerts (seconds)")
    parser.add_argument("--api", dest="api", default=os.environ.get("API_URL", "http://localhost:8000"))
    args = parser.parse_args()

    raw_assets = os.environ.get("BASE_ASSETS", "BTC-USD,SOL-USD,SUI-USD").split(",")
    base_assets = [asset.strip().strip('\"[] ') for asset in raw_assets if asset.strip()]
    secret = os.environ.get("WEBHOOK_SECRET", "changeme")

    with httpx.Client() as client:
        for _ in range(args.count):
            symbol = random.choice(base_assets)
            side = random.choice(["buy", "sell"])
            price = round(random.uniform(50, 40000), 2)
            alert = build_alert(symbol.strip(), side, price)
            body = json.dumps(alert).encode()
            signature = sign(body, secret)
            response = client.post(
                f"{args.api.rstrip('/')}/webhook/tradingview",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature,
                },
                timeout=10,
            )
            print(symbol, side, price, response.status_code, response.text)
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
