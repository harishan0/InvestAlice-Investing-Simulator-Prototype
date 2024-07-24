from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    # portfolios = db.relationship('Portfolio', backref='user', lazy=True)
    # transactions = db.relationship('TransactionHistory', backref='user', lazy=True)
    # cash = db.Column(db.Float, nullable=False)
    # value = db.Column(db.Float, nullable=False)
    # revenue = db.Column(db.Float, nullable=False)

    def __repr__(self): 
        return '<Username %r>' % self.username
    
'''
class Portfolio(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock = db.Column(db.String(20), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    purchasePrice = db.Column(db.Float, nullable=False)
    currentPrice = db.Column(db.Float, nullable=False)
    totalValue = db.Column(db.Float, nullable=False)

class TransactionHistory(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(5), nullable=False)
    stock = db.Column(db.String(20), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
'''    