import os

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.services.idempotency import throttle_symbol  # noqa: E402


def test_throttle_symbol_blocks_second_call():
    assert throttle_symbol("BTC-USD", 60) is True
    assert throttle_symbol("BTC-USD", 60) is False
