
# 8) Runtime & Strategy

- Per-symbol trader thread (`symbol_trader`) syncs to candle opens.
- **Trade mode**: 'follow' vs 'opposite' (previous candle color → side).
- **Run modes**:
  - **ongoing**: every candle open → one trade; closes at candle close (unless SL/TP).
  - **limit**: same, but stops creating new entries after `max_trades_limit` per run.
- **Push**: no new entry after current closes (runtime flag).
- **Close**: immediate cancel + market-close via Binance helper.
- **Recovery** (planned hook): if last ROI < threshold → next_margin = fixed + last_margin (capped by max).

> Extend `should_open_new_trade(...)` and the trade loop for full recovery/targets/SL shifting logic.
