import os
from flask import Flask

DEBUG = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///kobuy-app.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
EXEMPT_METHODS = {"OPTIONS"}
SECRET_KEY = os.urandom(100)
app = Flask(__name__)