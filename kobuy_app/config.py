import os
from flask import Flask

# 本番環境では絶対にデバッグモードを有効にしないこと。
# Werkzeugのデバッガが有効だと、例外発生時に対話型コンソールが露出し
# リモートコード実行(RCE)につながる致命的な脆弱性となる。
# 開発時のみ環境変数 FLASK_DEBUG=1 を指定して有効化する。
DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
SQLALCHEMY_DATABASE_URI = 'sqlite:///kobuy-app.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
EXEMPT_METHODS = {"OPTIONS"}
SECRET_KEY = os.urandom(100)

# VAPID設定（Web Push通知用）
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'your-vapid-private-key')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'your-vapid-public-key')

app = Flask(__name__)