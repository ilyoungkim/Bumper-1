class InvalidUser(Exception):
	""" The given details are not valid """
	def __init__(self, message, username, password):
		super().__init__(message)
		self.username = username
		self.password = password

class InvalidThread(Exception):
	""" The given thread is invalid """
	def __init__(self, message, thread):
		super().__init__(message)
		self.thread = thread

""" Configuration errors """
class ConfigError(Exception):
	""" Base for configuration errors """
	def __init__(self, message):
		super().__init__(message)

class InvalidConfig(ConfigError):
	""" Loaded config string is incorrect """
	pass

class MissingData(ConfigError):
	""" Missing information in the data """
	pass

class InvalidType(ConfigError):
	""" Invalid data type of a value """
	def __init__(self, message, item):
		super().__init__(message)
		self.item = item