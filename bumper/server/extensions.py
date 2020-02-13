from flask_pymongo import PyMongo
from flask_session import Session
from flask_bcrypt import Bcrypt

session = Session()
mongo = PyMongo()
bcrypt = Bcrypt()