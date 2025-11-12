from prometheus_client import Counter, Histogram

request_latency = Histogram(
    "tradingbot_request_latency_seconds", "HTTP request latency", ["method", "endpoint"]
)
alerts_received = Counter("tradingbot_alerts_received_total", "Trading alerts received")
orders_sent = Counter("tradingbot_orders_sent_total", "Orders submitted")
orders_filled = Counter("tradingbot_orders_filled_total", "Orders filled")
risk_blocked = Counter("tradingbot_risk_blocked_total", "Alerts blocked by risk")
trade_latency = Histogram("tradingbot_trade_latency_seconds", "Trade task latency")
