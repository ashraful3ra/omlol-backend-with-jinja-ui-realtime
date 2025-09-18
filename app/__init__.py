from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flasgger import Swagger
import os
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
socketio = SocketIO(async_mode='eventlet')

# ---- Realtime summary broadcaster (module-level) ----
def _summary_broadcaster(app):
    from .models import Trade
    from .bot_logic import running_bots
    with app.app_context():
        while True:
            try:
                running_ids = list(running_bots.keys())
                for bot_id in running_ids:
                    trades = Trade.query.filter(Trade.bot_id == bot_id).all()
                    total = len(trades)
                    wins = sum(1 for t in trades if (t.pnl or 0) > 0)
                    losses = sum(1 for t in trades if (t.pnl or 0) < 0)
                    breakeven = total - wins - losses
                    profit = sum(max(0.0, (t.pnl or 0.0)) for t in trades)
                    loss = sum(min(0.0, (t.pnl or 0.0)) for t in trades)
                    net = profit + loss
                    socketio.emit('summary_snapshot', {
                        'bot_id': bot_id,
                        'total_trades': total,
                        'win_trades': wins,
                        'loss_trades': losses,
                        'breakeven_trades': breakeven,
                        'total_profit': round(profit, 2),
                        'total_loss': round(loss, 2),
                        'net_pnl': round(net, 2),
                    })
            except Exception:
                pass
            socketio.sleep(3)

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    app.config.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev'))
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"))
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('SWAGGER', {'title': 'Omlol Bot API', 'uiversion': 3})

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')
    Swagger(app)

    from .accounts.routes import accounts_bp
    from .bots.routes import bots_bp
    from .trades.routes import trades_bp
    from .web.routes import web_bp

    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(bots_bp, url_prefix='/')
    app.register_blueprint(trades_bp, url_prefix='/')
    app.register_blueprint(web_bp, url_prefix='/')

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

    if not getattr(app, '_summary_broadcaster_started', False):
        socketio.start_background_task(_summary_broadcaster, app)
        app._summary_broadcaster_started = True

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({'success': False, 'error': str(e)}), e.code
        return jsonify({'success': False, 'error': str(e)}), 500

    return app
