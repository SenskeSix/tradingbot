# Architecture

## Components

- **FastAPI API** – Receives TradingView webhooks, validates auth, persists alerts, exposes health/metrics/reports.
- **Celery Worker** – Executes trade pipeline with Coinbase + risk modules.
- **Celery Beat** – Placeholder for scheduled jobs (future position audits, reconciliations).
- **PostgreSQL** – Persists alerts, orders, fills, risk events, positions.
- **Redis** – Celery broker + symbol throttling cache.
- **Prometheus/Grafana** – Metrics scraping + dashboard (see `docker/grafana-dashboard.json`).

## Sequence (Alert → Trade)

1. TradingView sends webhook to `/webhook/tradingview` with signed payload.
2. API verifies HMAC, validates schema, writes alert row.
3. Celery task `enqueue_trade_task` enqueues; worker loads alert + locks symbol throttle via Redis.
4. Market data fetch (Coinbase best bid/ask) informs sizing.
5. Risk engine enforces:
   - Max position percentage of NAV per asset.
   - Max daily notional risk budget.
   - Slippage guard vs price in alert.
6. Paper mode: fill recorded locally (orders/fills/positions). Live mode: Coinbase order placement + fill reconciliation.
7. Metrics counters updated (alerts, orders, risk blocks, latency) and JSON logs include `alert_id`, `symbol`, `side`.

## Risk Model

| Check | Formula | Config |
| --- | --- | --- |
| Position limit | `(existing_notional + proposed_qty * price) <= NAV * MAX_POS_PCT` | `MAX_POS_PCT` |
| Daily risk | `daily_notional + notional <= NAV * MAX_DAILY_RISK_PCT` | `MAX_DAILY_RISK_PCT` |
| Slippage | `abs(market - alert) / alert <= ORDER_SLIPPAGE_PCT` | `ORDER_SLIPPAGE_PCT` |
| Throttle | 1 order per symbol per `THROTTLE_SECONDS` | `THROTTLE_SECONDS` |

NAV defaults to `PAPER_CASH_USD` for paper mode; extend to live balances via Coinbase accounts API.
