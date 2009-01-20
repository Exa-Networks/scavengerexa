from zope.interface import implements
from config import IHandlerConfig, ConfigError

class Server:
	implements(IHandlerConfig)

	def __init__(self, name, **args):
		self.name = name
		self.auth_addr = args.get('auth_addr')
		self.acct_addr = args.get('acct_addr')
		# XXX: do not hard code _any_ values like this - at least not here
		self.dictionary = args.get('dictionary', '/etc/radius/dictionaries')
		self.clients = args.get('clients')
		self.handlers = args.get('handlers')
