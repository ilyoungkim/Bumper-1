class Config(object):
	DEBUG = False
	TESTING = False
	SECRET_KEY = b"secret_key_here"
	SESSION_TYPE = "mongodb"

class ProductionConfig(Config):
	MONGO_URI = "mongodb://localhost:27017/production"

class DevelopmentConfig(Config):
	MONGO_URI = "mongodb://localhost:27017/development"
	DEBUG = True