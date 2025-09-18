
from flask import Blueprint, request, jsonify
from ..models import Account
from .. import db
from binance.client import Client

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/accounts')
def accounts_page():
    """Accounts endpoint root
    ---
      tags:
        - Accounts
      responses:
        200:
          description: OK
    """
    return jsonify({"success": True, "message": "Accounts API root"})

@accounts_bp.route('/api', methods=['GET'])
@accounts_bp.route('/api/accounts', methods=['GET'])
def list_accounts():
    """List accounts
    ---
      tags:
        - Accounts
      responses:
        200:
          description: Account list
    """
    items = Account.query.all()
    return jsonify({
        'success': True,
        'accounts': [{
            'id': a.id,
            'name': a.name,
            'is_testnet': a.is_testnet
        } for a in items]
    })

@accounts_bp.route('/api', methods=['POST'])
def create_account():
    """Create account
    ---
      tags:
        - Accounts
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        200:
          description: Created
    """
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'name required'}), 400

    acc = Account(name=name,
                  api_key=data.get('api_key') or '',
                  api_secret=data.get('api_secret') or '',
                  is_testnet=bool(data.get('is_testnet')))
    db.session.add(acc)
    db.session.commit()

    # quick (best-effort) verify: try a harmless leverage change on BTCUSDT (ignored on failure)
    verified = False
    try:
        client = Client(acc.api_key, acc.api_secret, testnet=acc.is_testnet)
        client.futures_change_leverage(symbol='BTCUSDT', leverage=1)
        verified = True
    except Exception:
        verified = False

    return jsonify({'success': True, 'id': acc.id, 'verified': verified})

@accounts_bp.route('/api/<int:acc_id>', methods=['GET'])
def get_account(acc_id):
    """Get account
    ---
      tags:
        - Accounts
      parameters:
        - in: path
          name: acc_id
          required: true
          schema: {type: integer}
    """
    acc = Account.query.get_or_404(acc_id)
    return jsonify({'success': True, 'account': {
        'id': acc.id,
        'name': acc.name,
        'is_testnet': acc.is_testnet
    }})

@accounts_bp.route('/api/<int:acc_id>', methods=['PUT','PATCH'])
def update_account(acc_id):
    """Update account
    ---
      tags:
        - Accounts
      parameters:
        - in: path
          name: acc_id
          required: true
          schema: {type: integer}
      requestBody:
        content:
          application/json:
            schema: {type: object}
    """
    acc = Account.query.get_or_404(acc_id)
    data = request.get_json(force=True) or {}
    if 'name' in data and data['name']:
        acc.name = data['name']
    if 'api_key' in data and data['api_key'] is not None:
        acc.api_key = data['api_key']
    if 'api_secret' in data and data['api_secret'] is not None:
        acc.api_secret = data['api_secret']
    if 'is_testnet' in data and data['is_testnet'] is not None:
        acc.is_testnet = bool(data['is_testnet'])
    db.session.commit()
    return jsonify({'success': True, 'id': acc.id})

@accounts_bp.route('/api/<int:acc_id>', methods=['DELETE'])
def delete_account(acc_id):
    """Delete account
    ---
      tags:
        - Accounts
      parameters:
        - in: path
          name: acc_id
          required: true
          schema: {type: integer}
    """
    acc = Account.query.get_or_404(acc_id)
    db.session.delete(acc)
    db.session.commit()
    return jsonify({'success': True})
