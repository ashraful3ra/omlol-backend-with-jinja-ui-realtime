
# 4) API — Accounts

## List
`GET /accounts/api/accounts` (alias: `GET /accounts/api`)
```bash
curl -s http://127.0.0.1:5000/accounts/api
```

## Create
`POST /accounts/api`
```bash
curl -s -X POST http://127.0.0.1:5000/accounts/api -H "Content-Type: application/json" -d '{
  "name":"Main",
  "api_key":"<KEY>",
  "api_secret":"<SECRET>",
  "is_testnet": true
}'
```

## Read One
`GET /accounts/api/{id}`

## Update
`PUT /accounts/api/{id}`

## Delete
`DELETE /accounts/api/{id}`
