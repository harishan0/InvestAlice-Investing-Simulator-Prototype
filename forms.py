from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class RegisterForm(FlaskForm): 
    username = StringField("Enter a username", validators=[DataRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'username'})
    password = PasswordField("Enter a password", validators=[DataRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'password'})
    submit = SubmitField('Register')

class LoginForm(FlaskForm): 
    username = StringField("Enter a username", validators=[DataRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'username'})
    password = PasswordField("Enter a password", validators=[DataRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'password'})
    submit = SubmitField('Login')

class SharesForm(FlaskForm): 
    shares = IntegerField("# of shares: ")
    submit = SubmitField('Confirm')


