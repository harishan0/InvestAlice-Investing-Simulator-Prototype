from flask import render_template, url_for, redirect, request, jsonify, flash
from app import app, db
from forms import RegisterForm, LoginForm, SharesForm
from models import User, Stock, Transaction

from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

import yfinance as yf

from apscheduler.schedulers.background import BackgroundScheduler

import pytz

admin = Admin(app, name='Admin-dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Stock, db.session))
admin.add_view(ModelView(Transaction, db.session))

scheduler = BackgroundScheduler()

# schedule database updates every 30s
# we need to update currentPrice for every single stock in the users portfolio
# after updating all the stocks, we need to recalculate the users portfolio value and their revenue 
def update_data(): 
    user_id = current_user.id
    with app.app_context():
        try:  
            stocks = Stock.query.filter_by(user_id = user_id).all()
            stock_sum = 0
            for stock in stocks: 
                ticker = yf.Ticker(stock.stock)
                stock.currentPrice = ticker.info['currentPrice']
                stock_sum += (stock.currentPrice * stock.shares)
                db.session.commit()
            user = User.query.filter_by(id = user_id).first()
            user.value = stock_sum
            user.revenue = user.cash - 5000 + user.value
            db.session.commit()
            print('data updated')
        except Exception as e: 
            print(f'an error occured {e}')


@app.route('/')
def home(): 
    portfolio = None
    if current_user.is_authenticated: 
        update_data()
        portfolio = Stock.query.filter_by(user_id = current_user.id)
    return render_template('index.html', portfolio=portfolio)

# ========================= USER AUTHENTICATION =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated: 
        form = LoginForm()
        if form.validate_on_submit(): 
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                if check_password_hash(user.password, form.password.data): 
                    login_user(user)
                    return redirect(url_for('home'))
                else:
                    flash('Incorrect password. Please try again.')
            else:
                flash('Username not found. Please try again.')
    else: 
        flash('You are already logged in')
        return redirect(url_for('home'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register(): 
    if current_user.is_authenticated: 
        flash('You are already logged in')
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit(): 
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if not user: 
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        else: 
            flash('Not a unique username! Please pick a new username')
            return redirect(url_for('register'))
    return render_template('register.html', form=form)
    
# =================================== STOCK BUYING/SELLING/SEARCHING =========================

@app.route('/search-stock', methods=['GET', 'POST'])
def search_stock(): 
    stock_info = None
    
    if request.method == 'POST': 
        stock_symbol = request.form['stock_symbol'].upper()
        return redirect(url_for('search_stock', stock_symbol=stock_symbol))
    
    stock_symbol = request.args.get('stock_symbol')
    if stock_symbol:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        try: 
            if 'symbol' in info and info['symbol'] == stock_symbol.upper(): 
                stock_info = {
                    'symbol': stock_symbol,
                    'company_name': info.get('shortName', 'N/A'),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'current_price': info.get('currentPrice', 'N/A'),
                    'previous_close': info.get('previousClose', 'N/A'),
                    'pe_ratio': info.get('trailingPE', 'N/A'),
                    'dividend_yield': info.get('dividendYield', 'N/A'),
                    '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                    '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                }
            else: 
                stock_info = None
        except Exception as e: 
            stock_info = None
    
    return render_template('stock_info.html', stock_info=stock_info)

@app.route('/buy-stock/<ticker>', methods=['GET', 'POST'])
def buystock(ticker):
    stock_price = request.args.get('stock_price')
    current_share = Stock.query.filter_by(stock=ticker, user_id=current_user.id).first()
    num_shares = 0
    if current_share:
        num_shares = current_share.shares
    form = SharesForm()
    if form.validate_on_submit():
        value = float(form.shares.data) * float(stock_price)
        if (float(current_user.cash) - value) < 0:
            return render_template('buy.html', form=form, price=stock_price, ticker=ticker, num_shares=num_shares, invalid=True)
        else:
            shares = float(form.shares.data)
            currentPrice = (yf.Ticker(ticker)).info['currentPrice']
            if current_share:
                current_share.shares += shares
                current_share.currentPrice = currentPrice
                current_share.totalValue = value
            else:
                s = Stock(owner=current_user, stock=ticker, shares=shares, currentPrice=currentPrice, totalValue=value)
                db.session.add(s)

            current_user.cash -= value

            type = 'BUY'
            revenue = -1 * value
            purchasePrice = float(stock_price)
            t = Transaction(owner=current_user, type=type, stock=ticker, shares=shares, price=purchasePrice, revenue=revenue)
            db.session.add(t)
            db.session.commit()
            update_data()
            return redirect(url_for('home'))

    return render_template('buy.html', form=form, price=stock_price, ticker=ticker, num_shares=num_shares, invalid=False)


@app.route('/sell-stock/<ticker>', methods=['GET', 'POST'])
def sellstock(ticker):
    form = SharesForm()
    stock_price = request.args.get('stock_price')
    stock = Stock.query.filter_by(stock=ticker, user_id=current_user.id).first()
    current_shares = 0

    if stock:
        current_shares = int(stock.shares)

    if form.validate_on_submit():
        if not stock:
            return render_template('purchaseerror.html')

        shares = float(form.shares.data)
        if shares > current_shares:
            return render_template('sell.html', form=form, price=stock_price, ticker=ticker, num_shares=current_shares, invalid=True)

        else:
            value = shares * float(stock_price)
            stock.shares -= shares
            stock.totalValue = stock.shares * stock.currentPrice
            if stock.shares == 0:
                db.session.delete(stock)
            current_user.cash += value

            type = 'SELL'
            price = float(stock_price)
            revenue = value
            t = Transaction(owner=current_user, type=type, stock=ticker, price=price, shares=shares, revenue=revenue)
            db.session.add(t)
            db.session.commit()
            update_data()
            return redirect(url_for('home'))

    return render_template('sell.html', form=form, price=stock_price, ticker=ticker, num_shares=current_shares, invalid=False)

@app.route('/transaction-history')
def transaction_history(): 
    history = None
    if current_user.is_authenticated: 
        update_data()
        timezone = request.cookies.get('timezone', 'UTC')
        history = Transaction.query.filter_by(user_id = current_user.id)
        for stock in history: 
            stock.date = stock.date.astimezone(pytz.timezone(timezone))
    return render_template('transaction-history.html', history=history)