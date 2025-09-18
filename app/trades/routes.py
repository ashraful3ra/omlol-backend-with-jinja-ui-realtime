
from flask import request, jsonify
from . import trades_bp
from ..models import Trade
from .. import db
from datetime import datetime

def parse_datetime(s):
    if not s:
        return None
    try:
        # Accept ISO-like 'YYYY-MM-DD HH:MM:SS' or date
        if 'T' in s:
            return datetime.fromisoformat(s.replace('Z',''))
        return datetime.fromisoformat(s + ' 00:00:00') if len(s) <= 10 else datetime.fromisoformat(s)
    except Exception:
        return None

@trades_bp.route('/api/trades', methods=['GET'])
def list_trades():
    """List historical trades
    ---
      tags:
        - Trades
      parameters:
        - in: query
          name: bot_id
          schema: {type: integer}
        - in: query
          name: symbol
          schema: {type: string}
        - in: query
          name: from
          schema: {type: string}
        - in: query
          name: to
          schema: {type: string}
        - in: query
          name: page
          schema: {type: integer}
        - in: query
          name: page_size
          schema: {type: integer}
    """
    q = Trade.query
    bot_id = request.args.get('bot_id', type=int)
    symbol = request.args.get('symbol', type=str)
    dt_from = parse_datetime(request.args.get('from'))
    dt_to = parse_datetime(request.args.get('to'))
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=50, type=int)

    if bot_id:
        q = q.filter(Trade.bot_id == bot_id)
    if symbol:
        q = q.filter(Trade.symbol == symbol)
    if dt_from:
        q = q.filter(Trade.entry_time >= dt_from)
    if dt_to:
        q = q.filter(Trade.exit_time <= dt_to)

    q = q.order_by(Trade.entry_time.desc())
    items = q.paginate(page=page, per_page=page_size, error_out=False)

    def row(t: Trade):
        return {
            'id': t.id,
            'bot_id': t.bot_id,
            'symbol': t.symbol,
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'entry_time': t.entry_time.isoformat() if t.entry_time else None,
            'exit_time': t.exit_time.isoformat() if t.exit_time else None,
            'margin_used': t.margin_used,
            'pnl': t.pnl,
            'roi_percent': t.roi_percent,
            'close_reason': t.close_reason,
            'side': t.side,
        }

    return jsonify({
        'success': True,
        'page': page,
        'page_size': page_size,
        'total': items.total,
        'items': [row(t) for t in items.items],
    })

@trades_bp.route('/api/trades/open', methods=['GET'])
def list_open_trades():
    """List open (running) trades
    ---
      tags:
        - Trades
      parameters:
        - in: query
          name: bot_id
          schema: {type: integer}
        - in: query
          name: symbol
          schema: {type: string}
    """
    q = Trade.query.filter(Trade.exit_time.is_(None))
    bot_id = request.args.get('bot_id', type=int)
    symbol = request.args.get('symbol', type=str)
    if bot_id:
        q = q.filter(Trade.bot_id == bot_id)
    if symbol:
        q = q.filter(Trade.symbol == symbol)
    q = q.order_by(Trade.entry_time.desc())
    items = q.all()

    def row(t: Trade):
        return {
            'id': t.id,
            'bot_id': t.bot_id,
            'symbol': t.symbol,
            'entry_price': t.entry_price,
            'entry_time': t.entry_time.isoformat() if t.entry_time else None,
            'margin_used': t.margin_used,
            'roi_percent': t.roi_percent,
            'side': t.side,
        }

    return jsonify({'success': True, 'items': [row(t) for t in items]})
