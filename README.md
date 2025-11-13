# TradingBot

FastAPI + Celery service that ingests TradingView alerts and routes them to Coinbase Advanced Trade with optional paper trading, guardrails, and observability.

## Quickstart (Paper Mode)

1. `cp .env.example .env` and update secrets.
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install --upgrade pip && pip install -e .[dev]`
4. `alembic upgrade head`
5. Run services:
   - `uvicorn app.main:app --reload`
   - `celery -A app.workers.tasks.celery_app worker -Q trades -l info`

Docker Compose:

```bash
make up
```

Then seed demo data:

```bash
python -m app.cli seed-demo
```

### Simulate TradingView Alert

```bash
BODY='{ "id":"123e4567-e89b-12d3-a456-426614174000","symbol":"BTC-USD","side":"buy","price":20000 }'
SIG=$(python - <<'PY'
import hashlib, hmac, os
body = bytes(os.environ.get('BODY', ''), 'utf-8')
print(hmac.new(b"${WEBHOOK_SECRET}", body, hashlib.sha256).hexdigest())
PY)
curl -X POST http://localhost:8000/webhook/tradingview \
  -H "X-Signature: $SIG" \
  -d "$BODY"
```

> Tip: TradingView’s native UI cannot set custom headers, so in production append `?token=<WEBHOOK_SECRET>` to the webhook URL (e.g. `https://tradingbot.example.com/webhook/tradingview?token=...`). The API still supports signed `X-Signature` headers if you forward alerts through a relay that can add them.

## Services

- `POST /webhook/tradingview` – Validates HMAC + schema, inserts alert, enqueues Celery trade task.
- `GET /healthz` – Build SHA, DB/Redis connectivity.
- `GET /metrics` – Prometheus metrics (alerts, orders, risk blocks, latency).
- `GET /reports/daily` – Protected via `X-Internal-Token`.

## Trading Pipeline

1. Worker fetches alert and enforces Redis throttle.
2. Market data fetched from Coinbase and sized by configurable fraction/ATR proxy.
3. Risk checks for position, daily notional, slippage.
4. Paper mode writes fills + positions locally; live mode hits Coinbase REST API.
5. Metrics/logs emitted throughout.

## Tests & Tooling

```bash
make fmt
make lint
make test
```

### Paper-mode smoke test

With the API + worker running locally, you can blast dummy alerts into the webhook:

```bash
source .venv/bin/activate
python scripts/send_mock_alerts.py --count 5 --delay 1
```

The script builds random BUY/SELL alerts for BTC/SOL/SUI, signs them with `WEBHOOK_SECRET`, and posts to `/webhook/tradingview`. Watch `celery-worker.log` to confirm paper fills.

## TradingView Alert Setup

See `ALERTS.md` for JSON templates, query parameter usage, and Pine Script example.

## Deployment Notes

- Docker images `api`, `worker`, `scheduler` (Celery beat) + `redis` + `postgres`.
- Alembic migrations automatically run via the API entrypoint.
- Grafana dashboard JSON under `docker/grafana-dashboard.json` ready to import.
