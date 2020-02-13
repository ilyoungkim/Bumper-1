class InvalidUser(Exception):
	""" The given details are not valid """
	pass

class InvalidThread(Exception):
	""" The given thread is invalid """
	pass

""" Configuration errors """
class ConfigError(Exception):
	""" Base for configuration errors """
	pass

class InvalidJSON(ConfigError):
	""" Loaded config's JSON is invalid """
	pass

class MissingData(ConfigError):
	""" Missing information in the data """
	pass

class InvalidType(ConfigError):
	""" Invalid data type of a value """
	pass