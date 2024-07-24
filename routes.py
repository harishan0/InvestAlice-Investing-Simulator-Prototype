from flask import render_template, url_for, redirect, request, jsonify
from app import app, db
from forms import RegisterForm, LoginForm
from models import User, Portfolio, TransactionHistory

from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

import yfinance as yf
import requests

admin = Admin(app, name='Admin-dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Portfolio, db.session))
admin.add_view(ModelView(TransactionHistory, db.session))

@app.route('/')
def home(): 
    return render_template('index.html')




def search_to_ticker(search): 
    API_KEY = 'cqgl859r01qompnrfvs0cqgl859r01qompnrfvsg'
    base_url = 'https://finnhub.io/api/v1/stock/symbol'

    params = {
        'exchange': 'US', 
        'token': API_KEY
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    for symbol in data: 
        if search.lower() in symbol['description'].lower(): 
            return symbol['symbol']
        
    return 'No matches found'

@app.route('/search-stock', methods=['GET', 'POST'])
def search_stock(): 
    stock_info = None
    if request.method == 'POST': 
        search = request.form['stock_symbol']

        stock_symbol = search_to_ticker(search).upper()
    

        if stock_symbol == 'NO MATCHES FOUND': 
            return render_template('search_error.html')
        stock = yf.Ticker(stock_symbol)

        stock_info = {
            'symbol': stock_symbol, 
            'current_price': stock.info['currentPrice'],
            '52_week_high': stock.info['fiftyTwoWeekHigh'], 
            '52_week_low': stock.info['fiftyTwoWeekLow'], 
            'market_cap': stock.info['marketCap']
        }
    return render_template('index.html', stock_info=stock_info)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): 
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data): 
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register(): 
    form=RegisterForm()
    if form.validate_on_submit(): 
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
    return render_template('register.html', form=form)