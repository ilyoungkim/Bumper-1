from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import required, length

class LoginForm(FlaskForm):
	username = StringField('Username: ', [required()])
	password = PasswordField('Password: ', [required()])