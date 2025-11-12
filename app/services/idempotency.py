from __future__ import annotations

import time

import redis

from app.config import get_settings


class _MemoryStore:
    def __init__(self) -> None:
        self.store: dict[str, tuple[int, int | None]] = {}

    def get(self, key: str):
        value = self.store.get(key)
        if not value:
            return None
        ts, expires_at = value
        if expires_at and expires_at < int(time.time()):
            self.store.pop(key, None)
            return None
        return str(ts).encode()

    def set(self, key: str, value: int, ex: int | None = None):
        expires_at = int(time.time()) + ex if ex else None
        self.store[key] = (value, expires_at)


settings = get_settings()
try:
    _redis_client = redis.Redis.from_url(settings.redis_url)
    _redis_client.ping()
except Exception:  # noqa: BLE001
    _redis_client = _MemoryStore()


def throttle_symbol(symbol: str, window_seconds: int) -> bool:
    key = f"throttle:{symbol}"
    now = int(time.time())
    last = _redis_client.get(key)
    if last and now - int(last) < window_seconds:
        return False
    _redis_client.set(key, now, ex=window_seconds)
    return True
