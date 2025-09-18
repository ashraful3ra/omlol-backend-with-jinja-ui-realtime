
# 10) cURL Examples

Start bot:
```bash
curl -s -X POST http://127.0.0.1:5000/api/bots/1/start
```

Pause after current:
```bash
curl -s -X POST http://127.0.0.1:5000/api/bots/1/push
```

Resume:
```bash
curl -s -X POST http://127.0.0.1:5000/api/bots/1/resume
```

Immediate close:
```bash
curl -s -X POST http://127.0.0.1:5000/api/bots/1/close
```

Trades history:
```bash
curl -s "http://127.0.0.1:5000/api/trades?bot_id=1&page=1&page_size=50"
```
