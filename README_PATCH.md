
# Patch: Missing API & Minimal Logic Hooks (2025-09-16)

This patch adds the missing API endpoints you requested and minimal runtime hooks:

## New/Updated Endpoints

### Bots
- `GET /api/bots/<id>` — full bot config
- `PUT /api/bots/<id>` — update bot by id
- `DELETE /api/bots/<id>` — delete bot
- `GET /api/bots/<id>/status` — running/pushed + symbols
- `POST /api/bots/<id>/close` — **immediate: cancels open orders + market-closes positions for all bot symbols**
- `POST /api/bots/<id>/push` — pause after current (no new entries)

### Trades
- `GET /api/trades?bot_id=&symbol=&from=&to=&page=&page_size=` — historical trades
- `GET /api/trades/open?bot_id=&symbol=` — currently open trades

### Accounts
- `GET /accounts/api/<id>`
- `PUT/PATCH /accounts/api/<id>`
- `DELETE /accounts/api/<id>`

## Notes
- `app/utils/binance_helper.py` centralizes Binance closing logic.
- `app/bot_logic.py` now contains `should_open_new_trade(...)` to honor **push** and **limit** run mode (minimal; extend inside your trade loop before creating a new order).
- No DB schema changes required; existing JSON fields (`conditions`, `roi_targets`) are returned intact.
- To fully implement recovery margin logic and dynamic ROI bucketing, extend `app/bot_logic.py` where your entry/exit decisions are made.



## Additional endpoints (v2)
- `POST /api/bots` — create bot (id-based, symbols array accepted)
- `POST /api/bots/<id>/stop` — stop threads only
- `POST /api/bots/<id>/resume` — clear push flag
- `POST /api/bots/<id>/cancel-orders` — cancel open orders without closing positions
- `GET  /api/bots/<id>/positions` — current futures position & open orders per symbol
- `GET  /accounts/api` — alias for accounts list
- **Already present earlier**: `PUT/PATCH /api/bots/<id>`, `DELETE /api/bots/<id>`, `GET/PUT/PATCH/DELETE /accounts/api/<id>`
