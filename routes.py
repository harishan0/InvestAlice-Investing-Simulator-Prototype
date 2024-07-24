from flask import render_template, url_for, redirect, request
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from forms import RegisterForm, LoginForm
from models import User#, Portfolio, TransactionHistory
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def home(): 
    return render_template('index.html')

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