
# 1) Overview

This backend powers a **Binance Futures bot dashboard** with multi-account, multi-symbol, timeframe-synced trading threads plus reporting.

**Key Features**
- Accounts CRUD with quick verification
- Bots CRUD (plus Start / Push / Resume / Stop / Close)
- Symbols fetch from Binance futures
- Trade logging endpoints (open & history)
- Live summaries (wins/losses/breakeven, P/L)
- Socket.IO events for live UI updates
- SQLite (default) via SQLAlchemy

**Base URL (dev):** `http://127.0.0.1:5000`
