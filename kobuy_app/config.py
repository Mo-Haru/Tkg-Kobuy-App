import os
from flask import Flask

DEBUG = True
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