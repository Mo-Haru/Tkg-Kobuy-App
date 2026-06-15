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
# CSRF保護を有効化する。これによりPOST/PUT/PATCH/DELETEはCSRFトークンが必須になる。
# フォームは {{ form.csrf_token }} を、AJAXは X-CSRFToken ヘッダーを送る必要がある。
csrf.init_app(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.after_request
def set_security_headers(response):
    """すべてのレスポンスに防御的なセキュリティヘッダーを付与する。"""
    # クリックジャッキング対策
    response.headers['X-Frame-Options'] = 'DENY'
    # MIMEタイプ推測によるXSSを防ぐ
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # リファラの過剰な送出を抑制
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # 不要なブラウザ機能を無効化
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=(), payment=()'
    )
    # Content-Security-Policy: 既定では同一オリジンのみ許可し、
    # アプリが利用する外部CDN(フォント/Bootstrap/Material Web)だけを明示的に許可する。
    # frame-ancestors/object-src/base-url を絞り、クリックジャッキングや
    # ベースタグ書き換えによる攻撃を防ぐ。
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://esm.run; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
        "img-src 'self' data:; "
        "connect-src 'self' https://esm.run; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "form-action 'self'"
    )
    # HTTPS接続のときのみHSTSを付与する
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
    return response
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