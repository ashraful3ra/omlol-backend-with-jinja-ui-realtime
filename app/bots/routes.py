
from flask import Blueprint, request, jsonify
from sqlalchemy import func
import threading, json

from ..models import Bot, Account, Trade
from .. import db, socketio
from ..bot_logic import running_bots, symbol_trader

bots_bp = Blueprint('bots', __name__)

@bots_bp.route('/')
@bots_bp.route('/dashboard')
def dashboard():
    """Dashboard index
    ---
      tags:
        - Bots
      responses:
        200:
          description: OK
    """
    total_bots = db.session.query(func.count(Bot.id)).scalar() or 0
    running = len(running_bots)
    return jsonify({'success': True, 'bots_total': total_bots, 'bots_running': running})

@bots_bp.route('/api/bots', methods=['GET'])
def get_bots():
    """List bots
    ---
      tags:
        - Bots
    """
    bots = Bot.query.all()
    items = []
    for b in bots:
        items.append({
            'id': b.id,
            'name': b.name,
            'status': b.status,
            'symbols': b.get_symbols_list(),
            'account_name': b.account.name if b.account else None,
            'is_testnet': b.account.is_testnet if b.account else None
        })
    return jsonify({'success': True, 'bots': items})

@bots_bp.route('/api/bots', methods=['POST'])
def create_bot():
    """Create bot
    ---
      tags:
        - Bots
      requestBody:
        required: true
        content:
          application/json:
            schema: {type: object}
    """
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'name required'}), 400
    if Bot.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'bot with same name exists'}), 400

    symbols = data.get('symbols') or []
    if isinstance(symbols, str):
        try:
            symbols = json.loads(symbols)
        except Exception:
            symbols = [s.strip() for s in symbols.split(',') if s.strip()]

    bot = Bot(
        name=name,
        account_id=data.get('account_id'),
        timeframe=data.get('timeframe'),
        symbols=json.dumps(symbols),
        trade_mode=data.get('trade_mode'),
        leverage=int(data.get('leverage') or 1),
        margin_mode=data.get('margin_mode'),
        margin_usd=float(data.get('margin_usd') or 0),
        recovery_roi_threshold=data.get('recovery_roi_threshold'),
        max_recovery_margin=data.get('max_recovery_margin'),
        roi_targets=json.dumps(data.get('roi_targets')) if data.get('roi_targets') is not None else None,
        conditions=json.dumps(data.get('conditions')) if data.get('conditions') is not None else None,
        run_mode=data.get('run_mode') or 'ongoing',
        max_trades_limit=data.get('max_trades_limit'),
        status='stopped'
    )
    db.session.add(bot)
    db.session.commit()
    return jsonify({'success': True, 'id': bot.id})

@bots_bp.route('/api/bots/<int:bot_id>', methods=['GET'])
def get_bot_detail(bot_id):
    """Get bot detail
    ---
      tags:
        - Bots
      parameters:
        - in: path
          name: bot_id
          required: true
          schema: {type: integer}
    """
    bot = Bot.query.get_or_404(bot_id)
    def parse(raw):
        if raw is None: return None
        try: return json.loads(raw)
        except Exception: return raw
    return jsonify({'success': True, 'bot': {
        'id': bot.id,
        'name': bot.name,
        'account_id': bot.account_id,
        'account_name': bot.account.name if bot.account else None,
        'is_testnet': bot.account.is_testnet if bot.account else None,
        'timeframe': bot.timeframe,
        'symbols': bot.get_symbols_list(),
        'trade_mode': bot.trade_mode,
        'leverage': bot.leverage,
        'margin_mode': bot.margin_mode,
        'margin_usd': bot.margin_usd,
        'recovery_roi_threshold': bot.recovery_roi_threshold,
        'max_recovery_margin': bot.max_recovery_margin,
        'roi_targets': parse(bot.roi_targets),
        'conditions': parse(bot.conditions),
        'run_mode': bot.run_mode,
        'max_trades_limit': bot.max_trades_limit,
        'status': bot.status
    }})

@bots_bp.route('/api/bots/<int:bot_id>', methods=['PUT','PATCH'])
def update_bot(bot_id):
    """Update bot
    ---
      tags:
        - Bots
    """
    bot = Bot.query.get_or_404(bot_id)
    data = request.get_json(force=True) or {}

    for key in ['name','account_id','timeframe','trade_mode','leverage','margin_mode',
                'margin_usd','recovery_roi_threshold','max_recovery_margin','run_mode','max_trades_limit','status']:
        if key in data and data[key] is not None:
            setattr(bot, key, data[key])

    if 'symbols' in data and data['symbols'] is not None:
        bot.symbols = json.dumps(data['symbols']) if isinstance(data['symbols'], (list,tuple)) else data['symbols']

    if 'roi_targets' in data and data['roi_targets'] is not None:
        bot.roi_targets = json.dumps(data['roi_targets']) if not isinstance(data['roi_targets'], str) else data['roi_targets']

    if 'conditions' in data and data['conditions'] is not None:
        bot.conditions = json.dumps(data['conditions']) if not isinstance(data['conditions'], str) else data['conditions']

    db.session.commit()
    return jsonify({'success': True, 'id': bot.id})

@bots_bp.route('/api/bots/<int:bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    """Delete bot
    ---
      tags:
        - Bots
    """
    bot = Bot.query.get_or_404(bot_id)
    db.session.delete(bot)
    db.session.commit()
    return jsonify({'success': True})

@bots_bp.route('/api/bot-setup', methods=['POST'])
def bot_setup():
    """Create/Update bot (legacy name-based)
    ---
      tags:
        - Bots
    """
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'name required'}), 400

    bot = Bot.query.filter_by(name=name).first()
    symbols = data.get('symbols') or []
    if isinstance(symbols, str):
        try:
            symbols = json.loads(symbols)
        except Exception:
            symbols = [s.strip() for s in symbols.split(',') if s.strip()]

    if not bot:
        bot = Bot(name=name, status='stopped')
        db.session.add(bot)

    # assign fields
    bot.account_id = data.get('account_id')
    bot.timeframe = data.get('timeframe')
    bot.symbols = json.dumps(symbols)
    bot.trade_mode = data.get('trade_mode')
    bot.leverage = int(data.get('leverage') or 1)
    bot.margin_mode = data.get('margin_mode')
    bot.margin_usd = float(data.get('margin_usd') or 0)
    bot.recovery_roi_threshold = data.get('recovery_roi_threshold')
    bot.max_recovery_margin = data.get('max_recovery_margin')
    bot.roi_targets = json.dumps(data.get('roi_targets')) if data.get('roi_targets') is not None else None
    bot.conditions = json.dumps(data.get('conditions')) if data.get('conditions') is not None else None
    bot.run_mode = data.get('run_mode') or 'ongoing'
    bot.max_trades_limit = data.get('max_trades_limit')

    db.session.commit()
    return jsonify({'success': True, 'id': bot.id})


@bots_bp.route('/api/symbols', methods=['GET'])
def get_symbols():
    """List futures symbols (USDT)
    ---
      tags:
        - Symbols
      parameters:
        - in: query
          name: account_id
          schema: {type: integer}
    """
    import requests
    acc_id = request.args.get('account_id', type=int)
    acc = Account.query.get_or_404(acc_id) if acc_id else Account.query.first()
    if not acc:
        return jsonify({'success': False, 'message': 'no account available'}), 400

    base = 'https://testnet.binancefuture.com' if acc.is_testnet else 'https://fapi.binance.com'
    url = f"{base}/fapi/v1/exchangeInfo"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        info = r.json()
        syms = [s['symbol'] for s in info.get('symbols', []) if s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING']
        return jsonify({'success': True, 'symbols': syms, 'source': base})
    except Exception as e:
        return jsonify({'success': False, 'message': f'symbol fetch failed: {e}', 'source': base}), 502

@bots_bp.route('/api/bots/<int:bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """Start bot
    ---
      tags:
        - Bots
    """
    bot = Bot.query.get_or_404(bot_id)
    if bot_id in running_bots:
        return jsonify({'success': False, 'message': 'Bot is already running'}), 400

    threads = {}
    stop_event = threading.Event()
    symbols = bot.get_symbols_list() or []
    for sym in symbols:
        t = threading.Thread(target=symbol_trader, args=(bot.id, sym, stop_event), daemon=True)
        t.start()
        threads[sym] = t

    running_bots[bot.id] = {'threads': threads, 'stop_event': stop_event, 'push': False}
    try:
        bot.status = 'running'; db.session.commit()
        socketio.emit('bot_status_update', {'bot_id': bot.id, 'status': 'running'})
    except Exception:
        pass
    return jsonify({'success': True, 'message': f"Bot '{bot.name}' started."})

@bots_bp.route('/api/bots/<int:bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """Stop bot (threads only)
    ---
      tags:
        - Bots
    """
    bot_info = running_bots.pop(bot_id, None)
    bot = Bot.query.get_or_404(bot_id)
    if bot_info:
        bot_info['stop_event'].set()
        for thread in bot_info['threads'].values():
            try:
                thread.join(timeout=5)
            except Exception:
                pass
    try:
        bot.status = 'stopped'; db.session.commit()
        socketio.emit('bot_status_update', {'bot_id': bot.id, 'status': 'stopped'})
    except Exception:
        pass
    return jsonify({'success': True, 'message': f"Bot '{bot.name}' stopped."})

@bots_bp.route('/api/bots/<int:bot_id>/push', methods=['POST'])
def push_bot(bot_id):
    """Push (pause after current)
    ---
      tags:
        - Bots
    """
    info = running_bots.get(bot_id)
    if not info:
        return jsonify({'success': False, 'message': 'bot not running'}), 400
    info['push'] = True
    running_bots[bot_id] = info
    socketio.emit('bot_status_update', {'bot_id': bot_id, 'push': True})
    return jsonify({'success': True, 'message': 'push activated (pause after current)'})

@bots_bp.route('/api/bots/<int:bot_id>/resume', methods=['POST'])
def resume_bot(bot_id):
    """Resume (clear push)
    ---
      tags:
        - Bots
    """
    info = running_bots.get(bot_id)
    if not info:
        return jsonify({'success': False, 'message': 'bot not running'}), 400
    info['push'] = False
    running_bots[bot_id] = info
    socketio.emit('bot_status_update', {'bot_id': bot_id, 'push': False})
    return jsonify({'success': True, 'message': 'push cleared (resume)'})

@bots_bp.route('/api/bots/<int:bot_id>/close', methods=['POST'])
def close_bot_positions(bot_id):
    """Immediate close: cancel orders + market-close positions
    ---
      tags:
        - Bots
    """
    from ..utils.binance_helper import get_client, close_positions_and_cancel_orders
    bot = Bot.query.get_or_404(bot_id)
    acc = bot.account
    client = get_client(acc.api_key, acc.api_secret, acc.is_testnet)
    symbols = bot.get_symbols_list()
    result = close_positions_and_cancel_orders(client, symbols)
    return jsonify({'success': True, 'result': result})

@bots_bp.route('/api/bots/<int:bot_id>/cancel-orders', methods=['POST'])
def cancel_orders(bot_id):
    """Cancel open orders (no close)
    ---
      tags:
        - Bots
    """
    from ..utils.binance_helper import get_client, cancel_all_open_orders
    bot = Bot.query.get_or_404(bot_id)
    acc = bot.account
    client = get_client(acc.api_key, acc.api_secret, acc.is_testnet)
    out = {'cancelled': [], 'errors': {}}
    for sym in bot.get_symbols_list():
        try:
            cancel_all_open_orders(client, sym); out['cancelled'].append(sym)
        except Exception as e:
            out['errors'][sym] = str(e)
    return jsonify({'success': True, 'result': out})

@bots_bp.route('/api/bots/<int:bot_id>/status', methods=['GET'])
def bot_status(bot_id):
    """Bot status (db + runtime)
    ---
      tags:
        - Bots
    """
    bot = Bot.query.get_or_404(bot_id)
    info = running_bots.get(bot_id) or {}
    status = {
        'id': bot.id,
        'name': bot.name,
        'db_status': bot.status,
        'running': bool(info),
        'push': bool(info.get('push', False)),
        'symbols': list(info.get('threads', {}).keys()) if info else bot.get_symbols_list(),
    }
    return jsonify({'success': True, 'status': status})

@bots_bp.route('/api/bots/<int:bot_id>/positions', methods=['GET'])
def positions(bot_id):
    """Positions snapshot
    ---
      tags:
        - Bots
    """
    from binance.client import Client
    bot = Bot.query.get_or_404(bot_id)
    acc = bot.account
    client = Client(acc.api_key, acc.api_secret, testnet=acc.is_testnet)
    data = []
    for sym in bot.get_symbols_list():
        try:
            pos = client.futures_position_information(symbol=sym)
            orders = client.futures_get_open_orders(symbol=sym)
            entry_price = float(pos[0].get('entryPrice', 0) or 0) if pos else 0.0
            amt = float(pos[0].get('positionAmt', 0) or 0) if pos else 0.0
            data.append({'symbol': sym, 'entry_price': entry_price, 'position_amt': amt, 'open_orders': orders})
        except Exception as e:
            data.append({'symbol': sym, 'error': str(e)})
    return jsonify({'success': True, 'positions': data})

def _build_summary(query):
    summary = {
        'total_trades': 0,
        'running_trades': 0,
        'loss_trades': 0,
        'loss_negative_roi_stoploss': 0,
        'loss_negative_roi_candle_close': 0,
        'win_trades': 0,
        'win_before_r2': 0,
        'win_between_r2_r3': 0,
        'win_between_r3_r4': 0,
        'win_between_r4_r5': 0,
        'win_after_r5': 0,
        'breakeven_trades': 0,
        'profit_total': 0.0,
        'loss_total': 0.0,
        'net_result': 0.0
    }
    items = query.all()
    for t in items:
        summary['total_trades'] += 1
        roi = t.roi_percent or 0.0
        pnl = t.pnl or 0.0
        reason = (t.close_reason or '').lower()
        if t.exit_time is None:
            summary['running_trades'] += 1
            continue
        if roi > 0:
            summary['win_trades'] += 1
            if roi < 5: summary['win_before_r2'] += 1
            elif roi < 15: summary['win_between_r2_r3'] += 1
            elif roi < 20: summary['win_between_r3_r4'] += 1
            elif roi < 25: summary['win_between_r4_r5'] += 1
            else: summary['win_after_r5'] += 1
            summary['profit_total'] += pnl if pnl > 0 else abs(roi) * (t.margin_used or 0)/100.0
        elif roi < 0:
            summary['loss_trades'] += 1
            if 'stop' in reason: summary['loss_negative_roi_stoploss'] += 1
            else: summary['loss_negative_roi_candle_close'] += 1
            summary['loss_total'] += abs(pnl) if pnl < 0 else abs(roi) * (t.margin_used or 0)/100.0
        else:
            summary['breakeven_trades'] += 1
    summary['net_result'] = summary['profit_total'] - summary['loss_total']
    return summary

@bots_bp.route('/api/reports/live-summary', methods=['GET'])
def live_summary():
    """Live summary (all bots)
    ---
      tags:
        - Reports
    """
    q = Trade.query
    return jsonify({'success': True, 'summary': _build_summary(q)})

@bots_bp.route('/api/reports/bot-summary/<int:bot_id>', methods=['GET'])
def bot_summary(bot_id):
    """Bot summary
    ---
      tags:
        - Reports
    """
    q = Trade.query.filter(Trade.bot_id == bot_id)
    return jsonify({'success': True, 'summary': _build_summary(q)})
