from flask import Flask, abort, redirect, flash, session, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from .config import EXEMPT_METHODS
from flask import current_app
# commit test OK

csrf = CSRFProtect()
app = Flask(__name__)
app.config.from_object('kobuy_app.config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# インスタンス化
login_manager = LoginManager()
# アプリをログイン機能を紐付ける
login_manager.init_app(app)
# 未ログインユーザーを転送する(ここでは'login'ビュー関数を指定)
login_manager.login_view = 'login'
# Userモデルをインポート
from kobuy_app.models.models import Agreement, User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        '''
        ログインしているユーザーが管理者か確認
        '''
        if not current_user.is_authenticated or not current_user.has_role("admin"):
            flash("permission denied", "error")
            return redirect("/")
        return f(*args, **kwargs)
    
    return decorated_function

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS or current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.is_authenticated:
            flash("このページにアクセスするにはログインしてください", "error")
            return current_app.login_manager.unauthorized()

        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view

def create_app():
    # Blueprintやその他の初期化処理はここで行います
    from kobuy_app.views import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app

def rule_required(r):
    @wraps(r)  # デコレーターを適切に扱うためのラッパー
    def decorated_fnc(*args, **kwargs):
        # 現在のユーザーの同意状況を確認
        agt = Agreement.query.filter_by(user_id=current_user.id).first()
        if not agt or not agt.agreed:
            # 同意がない場合、ルールページへリダイレクト
            return redirect(url_for('rule'))
        return r(*args, **kwargs)  # 元の関数を呼び出す
    
    return decorated_fnc