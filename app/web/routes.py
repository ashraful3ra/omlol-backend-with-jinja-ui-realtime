
from flask import Blueprint, render_template
from ..models import Bot, Account, Trade
from .. import db

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static', static_url_path='/app/static')

@web_bp.route('/app')
def home():
    return render_template('dashboard.html', page='dashboard')

@web_bp.route('/app/bot')
def bot_page():
    return render_template('bot.html', page='bot')

@web_bp.route('/app/report')
def report_page():
    return render_template('report.html', page='report')

@web_bp.route('/app/account')
def account_page():
    return render_template('account.html', page='account')
