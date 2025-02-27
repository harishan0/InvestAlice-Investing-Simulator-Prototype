from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.config['SECRET_KEY'] = 'InvestAlicePrototype'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id): 
    from models import User
    return User.query.get(int(user_id))

from routes import *


if(__name__) == '__main__': 
    app.run(debug=True)