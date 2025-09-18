
# 3) Data Models (SQLAlchemy)

## Account
| Field      | Type      | Notes               |
|------------|-----------|---------------------|
| id         | Integer   | PK                  |
| name       | String    | unique              |
| api_key    | String    |                     |
| api_secret | String    |                     |
| is_testnet | Boolean   | default False       |

## Bot
| Field                   | Type     | Notes |
|-------------------------|----------|-------|
| id                      | Integer  | PK |
| name                    | String   | unique |
| account_id              | Integer  | FK -> Account.id |
| timeframe               | String   | '1m','5m','15m','30m','1h','4h' |
| symbols                 | Text(JSON) | ["BTCUSDT",...] |
| trade_mode              | String   | 'follow'|'opposite' |
| leverage                | Integer  | 1..150 |
| margin_mode             | String   | 'normal'|'recovery' |
| margin_usd              | Float    | fixed margin per entry |
| recovery_roi_threshold  | Float    | recovery trigger ROI% |
| max_recovery_margin     | Float    | cap in USD |
| roi_targets             | Text(JSON) | e.g. {{"R2":0,"R3":15,"R4":20,"R5":25}} |
| conditions              | Text(JSON) | open/close toggles |
| run_mode                | String   | 'ongoing'|'limit' |
| max_trades_limit        | Integer  | for limit mode |
| status                  | String   | 'running'|'stopped' |
| created_at              | DateTime | |

## Trade
| Field        | Type    | Notes |
|--------------|---------|-------|
| id           | Integer | PK |
| bot_id       | Integer | FK -> Bot.id |
| symbol       | String  | |
| entry_price  | Float   | |
| exit_price   | Float   | |
| entry_time   | DateTime| default now |
| exit_time    | DateTime| nullable (open) |
| margin_used  | Float   | USD |
| pnl          | Float   | signed USD |
| roi_percent  | Float   | signed % |
| close_reason | String  | e.g. 'stoploss_hit','candle_close','tp_R5','breakeven' |
| side         | String  | 'LONG'|'SHORT' |
