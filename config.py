import os

class Config: 
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False