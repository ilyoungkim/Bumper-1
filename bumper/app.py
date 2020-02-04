import threading
from flask import Flask

from .admin.controllers import admin
from .api.controllers import api
from .auth.controllers import auth

from .config import DevelopmentConfig, ProductionConfig
from .extensions import session, mongo, bcrypt

def create_app():
	app = Flask(__name__, static_url_path='/static')

	load_configurations(app)
	initialise_extensions(app)
	register_blueprints(app)

	return app

def load_configurations(app):
	app.config.from_object(ProductionConfig)

def initialise_extensions(app):
	session.init_app(app)
	mongo.init_app(app)
	bcrypt.init_app(app)

def register_blueprints(app):
	app.register_blueprint(admin)
	app.register_blueprint(api)
	app.register_blueprint(auth)