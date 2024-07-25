from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

    stocks = db.relationship('Stock', backref='owner', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='owner', lazy=True, cascade="all, delete-orphan")

    cash = db.Column(db.Float, default=5000, nullable=False)
    # total value coming from all stocks 
    value = db.Column(db.Float, default=0, nullable=False)
    revenue = db.Column(db.Float, default=0, nullable=False)

    def __repr__(self): 
        return '<Username %r>' % self.username
    

class Stock(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock = db.Column(db.String(20), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    currentPrice = db.Column(db.Float, nullable=False)
    totalValue = db.Column(db.Float, nullable=False)

class Transaction(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(5), nullable=False)
    stock = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
   