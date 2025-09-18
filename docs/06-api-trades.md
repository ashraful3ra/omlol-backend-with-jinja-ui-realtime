
# 6) API — Trades

## List historical
`GET /api/trades?bot_id=&symbol=&from=&to=&page=&page_size=`
```bash
curl -s "http://127.0.0.1:5000/api/trades?bot_id=1&page=1&page_size=50"
```

## List open
`GET /api/trades/open?bot_id=&symbol=`
```bash
curl -s "http://127.0.0.1:5000/api/trades/open?bot_id=1"
```
