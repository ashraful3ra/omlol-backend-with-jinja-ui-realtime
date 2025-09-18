
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flasgger import Swagger
import os
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    # Basic config
    app.config['SECRET_KEY'] = 'a_super_secret_key_for_production_change_it'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ---- Swagger Template for Section-wise Tags ----
    swagger_template = {
        "swagger": "2.0",
        "host": "127.0.0.1:5000",
        "basePath": "/",
        "schemes": ["http"],
        "info": {
            "title": "Trading Bot API",
            "description": "Section-wise grouped API documentation",
            "version": "1.0.0"
        },
        "tags": [
            {"name": "Accounts", "description": "Manage exchange accounts"},
            {"name": "Bots", "description": "Create, configure, and control bots"},
            {"name": "Trades", "description": "Trade history and open trades"},
            {"name": "Symbols", "description": "Symbols from Binance Futures"},
            {"name": "Reports", "description": "Live/summary reporting"}
        ]
    }
    app.config['SWAGGER'] = {'uiversion': 3, 'title': 'Trading Bot API', 'specs_route': '/apidocs/'}

    # Init extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    Swagger(app, template=swagger_template)

    # DB create
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    # Blueprints
    from .accounts.routes import accounts_bp
    from .bots.routes import bots_bp
    from .trades.routes import trades_bp
    from .web.routes import web_bp

    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(bots_bp, url_prefix='/')
    app.register_blueprint(trades_bp, url_prefix='/')
    app.register_blueprint(web_bp, url_prefix='/')

    # ---- JSON error handler (so Swagger/UI always gets JSON) ----
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({'success': False, 'error': str(e)}), e.code
        return jsonify({'success': False, 'error': str(e)}), 500

    return app
