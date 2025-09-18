
# 5) API — Bots

## List
`GET /api/bots`

## Create (id-based)
`POST /api/bots`
```bash
curl -s -X POST http://127.0.0.1:5000/api/bots -H "Content-Type: application/json" -d '{
  "name":"BNB-1m",
  "account_id":1,
  "timeframe":"1m",
  "symbols":["BNBUSDT"],
  "trade_mode":"follow",
  "leverage":5,
  "margin_mode":"normal",
  "margin_usd":10,
  "roi_targets": {"R2":0,"R3":15,"R4":20,"R5":25},
  "conditions": {"open_at_candle_open": true, "close_at_candle_close": true},
  "run_mode":"ongoing"
}'
```

> Legacy: `POST /api/bot-setup` (name-based create/update)

## Detail
`GET /api/bots/{id}`

## Update
`PUT /api/bots/{id}`

## Delete
`DELETE /api/bots/{id}`

## Start / Push / Resume / Stop / Close
- `POST /api/bots/{id}/start` — start threads per symbol
- `POST /api/bots/{id}/push` — pause-after-current (**no new entries**)
- `POST /api/bots/{id}/resume` — clear push flag
- `POST /api/bots/{id}/stop` — stop threads (does **not** close positions)
- `POST /api/bots/{id}/close` — **cancel all open orders + close positions** (per symbol)

## Status & Positions
- `GET /api/bots/{id}/status` — db status + runtime flags
- `GET /api/bots/{id}/positions` — current position + open orders
- `POST /api/bots/{id}/cancel-orders` — only cancel orders
