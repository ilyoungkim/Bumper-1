from flask import Blueprint, redirect, url_for

home = Blueprint('index', __name__)

@home.route('/')
def index():
	return redirect(url_for('auth.login'))