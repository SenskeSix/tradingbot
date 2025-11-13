# TradingView Alerts

## Webhook URL

```
https://<host>/webhook/tradingview?token=<WEBHOOK_SECRET>
```

- TradingView cannot add custom headers, so append `?token=<WEBHOOK_SECRET>` to the webhook URL for auth.
- If you have a relay that can sign requests, you may still send `X-Signature` (HMAC) or `Authorization: Bearer <WEBHOOK_SECRET>` headers instead of the query param.

## JSON Template

```json
{
  "id": "{{alert_id}}",
  "symbol": "{{ticker}}",     // BTC-USD | SOL-USD | SUI-USD
  "side": "buy",              // buy | sell | flat
  "confidence": {{strategy.order.comment_value}},
  "timeframe": "{{interval}}",
  "price": {{close}},
  "ts": "{{timenow}}"
}
```

## Example Pine Script Snippet

```pinescript
//@version=5
strategy("EMA ATR Bot", overlay=true, process_orders_on_close=true)
fast = ta.ema(close, 21)
slow = ta.ema(close, 55)
atr = ta.atr(14)
longCond = ta.crossover(fast, slow)
shortCond = ta.crossunder(fast, slow)

if longCond
    alert('{"id":"{{ticker}}-{{timenow}}","symbol":"{{ticker}}","side":"buy","price":{{close}},"confidence":{{strategy.order.comment_value}}}', alert.freq_once_per_bar_close)
if shortCond
    alert('{"id":"{{ticker}}-{{timenow}}","symbol":"{{ticker}}","side":"sell","price":{{close}}}', alert.freq_once_per_bar_close)
```

Add the webhook URL + headers in the TradingView alert dialog.
