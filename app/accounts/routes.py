from flask import Blueprint, request, jsonify
from ..models import Account
from .. import db
from binance.client import Client

accounts_bp = Blueprint('accounts', __name__)

# --- Helpers ---
def _client_for(acc: Account) -> Client:
    """Return a python-binance Client configured for UM-Futures; supports testnet."""
    client = Client(acc.api_key, acc.api_secret, testnet=bool(acc.is_testnet))
    if acc.is_testnet:
        try:
            client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
            client.FUTURES_DATA_URL = 'https://testnet.binancefuture.com/futures/data'
        except Exception:
            pass
    return client

def _usdt_futures_balance(client: Client):
    """Fetch USDT balance for UM-Futures. Returns float or None on failure."""
    try:
        balances = client.futures_account_balance()
        usdt = next((b for b in balances if b.get('asset') == 'USDT'), None)
        if not usdt:
            return None
        val = usdt.get('withdrawAvailable') or usdt.get('balance') or 0
        return float(val)
    except Exception:
        return None

@accounts_bp.route('/accounts')
def accounts_root():
    return jsonify({'success': True, 'message': 'Accounts root'})

@accounts_bp.route('/api', methods=['GET'])
@accounts_bp.route('/api/accounts', methods=['GET'])
def list_accounts():
    """
    List accounts (with USDT-M Futures balance)
    ---
      tags: [Accounts]
      summary: List accounts with Binance USDT-M Futures balance
      responses:
        200:
          description: OK
          content:
            application/json:
              example:
                success: true
                accounts:
                  - id: 1
                    name: TestDev
                    is_testnet: true
                    balance: 1234.56
    """
    items = []
    for acc in Account.query.order_by(Account.id.desc()).all():
        bal = None
        try:
            client = _client_for(acc)
            bal = _usdt_futures_balance(client)
        except Exception:
            bal = None
        items.append({
            'id': acc.id,
            'name': acc.name,
            'is_testnet': bool(acc.is_testnet),
            'balance': round(bal, 2) if isinstance(bal, (int, float)) else None,
        })
    return jsonify({'success': True, 'accounts': items})

@accounts_bp.route('/api', methods=['POST'])
@accounts_bp.route('/api/accounts', methods=['POST'])
def create_account():
    """
    Create account
    ---
      tags: [Accounts]
      summary: Create a new account (optionally Testnet)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name: {type: string}
                api_key: {type: string}
                api_secret: {type: string}
                is_testnet: {type: boolean}
      responses:
        200:
          description: Created
          content:
            application/json:
              example:
                success: true
                account:
                  id: 1
                  name: TestDev
                  is_testnet: true
                  verified: true
    """
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    api_key = (data.get('api_key') or '').strip()
    api_secret = (data.get('api_secret') or '').strip()
    is_testnet = bool(data.get('is_testnet'))

    if not name or not api_key or not api_secret:
        return jsonify({'success': False, 'message': 'name, api_key and api_secret required'}), 400
    if Account.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'account name already exists'}), 409

    acc = Account(name=name, api_key=api_key, api_secret=api_secret, is_testnet=is_testnet)
    db.session.add(acc)
    db.session.commit()

    ok = True
    try:
        client = _client_for(acc)
        client.futures_exchange_info()
    except Exception:
        ok = False

    return jsonify({'success': True, 'account': {
        'id': acc.id,
        'name': acc.name,
        'is_testnet': acc.is_testnet,
        'verified': ok
    }})

@accounts_bp.route('/api/<int:acc_id>', methods=['DELETE'])
def delete_account(acc_id):
    """
    Delete account
    ---
      tags: [Accounts]
      parameters:
        - in: path
          name: acc_id
          required: true
          schema: {type: integer}
      responses:
        200:
          description: OK
    """
    acc = Account.query.get_or_404(acc_id)
    db.session.delete(acc)
    db.session.commit()
    return jsonify({'success': True})

@accounts_bp.route('/api/<int:acc_id>/balance', methods=['GET'])
def fetch_balance(acc_id):
    """
    Get USDT-M Futures balance for one account
    ---
      tags: [Accounts]
      summary: Fetch account balance (USDT) from Binance Futures
      parameters:
        - in: path
          name: acc_id
          required: true
          schema: {type: integer}
      responses:
        200:
          description: OK
          content:
            application/json:
              example:
                success: true
                balance: 1234.56
    """
    acc = Account.query.get_or_404(acc_id)
    client = _client_for(acc)
    bal = _usdt_futures_balance(client)
    return jsonify({'success': True, 'balance': round(bal, 2) if isinstance(bal, (int, float)) else None})
