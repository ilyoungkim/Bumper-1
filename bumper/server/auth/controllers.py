from flask import ( Blueprint, session, render_template, 
					url_for, redirect, abort )

from .forms import LoginForm
from ..extensions import mongo, bcrypt

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
	if mongo.db.admin.find() == 0:
		return redirect(url_for('auth.register'))
	form = LoginForm()
	if form.validate_on_submit():
		user = mongo.db.admin.find_one({'username': form.username.data})
		if user and bcrypt.check_password_hash(user['password'], form.password.data):
			session['uid'] = user['_id']
			return redirect(url_for('admin.index'))

	return render_template('auth/login.html', form=form, mode='login')

@auth.route('/logout', methods=['GET'])
def logout():
	session.pop('uid', None)
	return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
	if mongo.db.admin.count() > 0:
		return redirect(url_for('auth.login'))

	form = LoginForm()
	if form.validate_on_submit():
		user = mongo.db.admin.find_one({'username': form.username.data})
		if not user:
			mongo.db.admin.insert_one({
				'username': form.username.data,
				'password': bcrypt.generate_password_hash(form.password.data)
			})
			user = mongo.db.admin.find_one({'username': form.username.data})
			session['uid'] = user['_id']
			return redirect(url_for('admin.index'))

	return render_template('auth/login.html', form=form, mode='register')