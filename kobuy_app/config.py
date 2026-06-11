import os
import secrets
from flask import Flask

# 本番環境では絶対にデバッグモードを有効にしないこと。
# Werkzeugのデバッガが有効だと、例外発生時に対話型コンソールが露出し
# リモートコード実行(RCE)につながる致命的な脆弱性となる。
# 開発時のみ環境変数 FLASK_DEBUG=1 を指定して有効化する。
DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///kobuy-app.db')
# パフォーマンスのため変更追跡は無効化（不要なオーバーヘッドと警告を防ぐ）
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
EXEMPT_METHODS = {"OPTIONS"}

# SECRET_KEY は環境変数から読み込むことを推奨。
# 設定が無い場合は起動ごとにランダム生成する(再起動でセッションは無効化される)。
# 本番では SECRET_KEY を固定の十分長いランダム値として環境変数で渡すこと。
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(64)

# ---------------- セッション/Cookie のセキュリティ ----------------
# JavaScript からセッションCookieを読めないようにする(XSSによる窃取を緩和)
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
# クロスサイトからのCookie送信を制限し、CSRFを緩和する
SESSION_COOKIE_SAMESITE = 'Lax'
REMEMBER_COOKIE_SAMESITE = 'Lax'
# HTTPS環境では必ず有効化する。HTTP(開発)では送信できなくなるため環境変数で切替。
# 本番(HTTPS)では SESSION_COOKIE_SECURE=1 を設定すること。
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

# ---------------- CSRF 保護 ----------------
WTF_CSRF_ENABLED = True
# トークンの有効期限を切らずセッション全体で有効にする(SPA的な操作での失効を防ぐ)
WTF_CSRF_TIME_LIMIT = None

# ---------------- アプリ固有の設定 ----------------
# 登録時の確認コード。ソースコードに直書きせず環境変数で管理する。
REGISTER_CONFIRM_CODE = os.environ.get('REGISTER_CONFIRM_CODE', '12345678')
# 登録を許可するメールアドレスのドメイン(カンマ区切り)
ALLOWED_EMAIL_DOMAINS = [
    d.strip()
    for d in os.environ.get('ALLOWED_EMAIL_DOMAINS', 'fukui-ed.jp').split(',')
    if d.strip()
]

# VAPID設定（Web Push通知用）
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')

app = Flask(__name__)
