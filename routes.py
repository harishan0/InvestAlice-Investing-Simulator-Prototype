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

admin = Admin(app, name='Admin-dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Stock, db.session))
admin.add_view(ModelView(Transaction, db.session))

scheduler = BackgroundScheduler()

# schedule database updates every 30s
# we need to update currentPrice for every single stock in the users portfolio
# after updating all the stocks, we need to recalculate the users portfolio value and their revenue 
def update_data(user_id): 
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



@app.before_request
def start_scheduler(): 
    app.before_request_funcs[None].remove(start_scheduler)
    scheduler.add_job(func=update_data, trigger='interval', seconds=30, args=[current_user.id]) 
    scheduler.start()

@app.route('/')
def home(): 
    portfolio = None
    if current_user.is_authenticated: 
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
    form=RegisterForm()
    if form.validate_on_submit(): 
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if not user: 
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('home'))
        else: 
            flash('Not a unique username! Please pick a new username')
            return redirect(url_for('register'))
    return render_template('register.html', form=form)
    
# =================================== STOCK BUYING/SELLING/SEARCHING =========================

# searching
@app.route('/search-stock', methods=['GET', 'POST'])
def search_stock(): 
    stock_info = None
    if request.method == 'POST': 
        stock_symbol = request.form['stock_symbol'].upper()
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        try: 
            if 'symbol' in info and info['symbol'] == stock_symbol.upper(): 
                stock_info = {
                    'symbol': stock_symbol, 
                    'current_price': info['currentPrice'],
                    '52_week_high': info['fiftyTwoWeekHigh'], 
                    '52_week_low': info['fiftyTwoWeekLow'], 
                    'market_cap': info['marketCap']
                }
            else: 
                return render_template('search_error.html')
        except Exception as e: 
            return render_template('search_error.html')
        
    return render_template('stock_info.html', stock_info=stock_info)

# buying
@app.route('/buy-stock', methods=['GET', 'POST'])
def buystock(): 
    stock_price = request.args.get('stock_price')
    ticker = request.args.get('ticker')
    current_share = Stock.query.filter_by(stock=ticker).first()
    num_shares=0
    if current_share: 
        num_shares = current_share.shares
    form = SharesForm()
    if form.validate_on_submit(): 
        value = float(form.shares.data) * float(stock_price)
        if (float(current_user.cash) - value) < 0: 
            return render_template('purchaseerror.html')
        else: 
            shares=float(form.shares.data)
            currentPrice=(yf.Ticker(ticker)).info['currentPrice']
            owner = current_user
            # if user already owns some shares, add more
            if current_share: 
                current_share.shares += shares
                current_share.currentPrice = currentPrice
                current_share.totalValue = value
            else: 
                # creating a stock item
                s = Stock(owner=owner, stock=ticker, shares=shares, currentPrice=currentPrice, totalValue=value)
                db.session.add(s)

            # updating user 
            current_user.cash -= value
            current_user.value += value

            # creating transaction history object 
            type='Buy'
            revenue = -1 * value
            purchasePrice=float(stock_price)
            t = Transaction(owner=owner, type=type, stock=ticker, shares=shares, price=purchasePrice, revenue=revenue)
            db.session.add(t)
            db.session.commit()
            return redirect(url_for('home'))
    
    return render_template('buy.html', form=form, price=stock_price, ticker=ticker, num_shares=num_shares)

# selling
@app.route('/sell-stock', methods=['GET', 'POST'])
def sellstock():
    form = SharesForm()
    stock_price = request.args.get('stock_price')
    ticker = request.args.get('ticker')
    stock = Stock.query.filter_by(stock=ticker).first()
    current_shares = 0

    if stock: 
        current_shares = int(stock.shares)
    
    if form.validate_on_submit(): 
        # user doesn't own any shares of stock
        if not stock: 
            return render_template('purchaseerror.html')
        
        shares = float(form.shares.data)
        if shares > current_shares: 
            # user wants to sell too many shares    
            return render_template('purchaseerror.html')
        
        else:
            # update stock values 
            value = shares * float(stock_price)
            stock.shares -= shares
            stock.totalValue = stock.shares * stock.currentPrice
            if stock.shares == 0: 
                db.session.delete(stock)
            # update user values 
            current_user.cash += value
            current_user.value -= value
            # create transaction 
            type='sell'
            price=float(stock_price)
            revenue=value
            t=Transaction(owner=current_user, type=type, stock=ticker, price=price, shares=shares, revenue=revenue)
            db.session.add(t)
            db.session.commit()
            return redirect(url_for('home'))
        
    return render_template('sell.html', form=form, price=stock_price, ticker=ticker, num_shares=current_shares)

@app.route('/transaction-history')
def transaction_history(): 
    history = None
    if current_user.is_authenticated: 
        history = Transaction.query.filter_by(user_id = current_user.id)
    return render_template('transaction-history.html', history=history)