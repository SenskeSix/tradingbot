from __future__ import annotations

import logging

from app.config import Settings, get_settings
from app.services.coinbase import CoinbaseClient

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(
        self, client: CoinbaseClient | None = None, settings: Settings | None = None
    ) -> None:
        self.client = client or CoinbaseClient(settings)
        self.settings = settings or get_settings()

    def get_mid_price(self, symbol: str, fallback: float | None = None) -> float:
        if self.settings.trading_mode == "paper" and not self.settings.coinbase_api_key:
            if fallback is not None:
                logger.info("using fallback price for %s in paper mode", symbol)
                return fallback
            return 0.0
        try:
            bid_ask = self.client.get_best_bid_ask(symbol)
        except Exception as exc:  # pragma: no cover - network dependent
            if fallback is not None:
                logger.warning("market data fallback", extra={"symbol": symbol, "error": str(exc)})
                return fallback
            raise
        if bid_ask.best_bid and bid_ask.best_ask:
            return (bid_ask.best_bid + bid_ask.best_ask) / 2
        return bid_ask.best_ask or bid_ask.best_bid or (fallback or 0.0)
