import os
import sys

# 仮想環境のPythonインタープリタのパスを設定
venv_python = '/var/www/Kobuy-Application/venv/bin/python3'

# システムのPython環境に仮想環境のライブラリを追加
if os.path.exists(venv_python):
    sys.path.insert(0, '/var/www/Kobuy-Application/venv/lib/python3.12/site-packages')

# Flaskアプリケーションのパスを追加
sys.path.insert(0, "/var/www/Kobuy-Application")

# Flaskアプリケーションのインポート
from kobuy_app import create_app

# WSGI用のapplicationオブジェクトを作成
application = create_app()
