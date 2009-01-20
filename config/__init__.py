from zope.interface import Interface, implements
from twisted.plugin import getPlugins, IPlugin

DICTIONARY_PATH='/home/david/devel/exa/app/radius/config/dictionaries'
import os

#from radius.config.manager import HandlerManager, ServerManager
from radius.config.manager import HandlerManager, ClientManager
from radius.packet.dictionary import RadiusDictionary

class ConfigError(Exception): pass

class IConfigPlugin(IPlugin):
	def create(*attributes, **named_attributes):
		""""""

class IClientConfig(IConfigPlugin):
	"""A client that is allowed to make requests of us"""

class IHandlerConfig(IConfigPlugin):
	"""Decide what to do with a request"""

class IPoolConfig(IConfigPlugin):
	"""Authentication and Authorisation"""

	def logon(packet, attributes):
		"""Authenticate the user and specify attributes to include in the response"""

	def logoff(packet):
		"""Free resources after a user disconnects"""



class ClientConfig:
	implements(IClientConfig)
	def __init__(self, name, addr, secret):
		self.name = name
		self.addr = addr
		self.secret = secret

	def __getitem__(self, item):
		return getattr(self, item)



#class ConfigPlugin:
#	def __init__(self):
#		pass 
#
#	def getModule(self):
#		return self.module


class GlobalConfig:
	def __init__(self):
		from config import clients, pools, handlers, servers

		self.servers = self.__getPlugins(servers)
		self.clients = self.__getPlugins(clients)
		self.pools = self.__getPlugins(pools)
		
		from config.aaa import authentication, accounting, authorisation

		self.authenticators = self.__getPlugins(authentication)
		self.accountants = self.__getPlugins(accounting)
		self.authorisers = self.__getPlugins(authorisation)

		from config import mangling
		self.manglers = self.__getPlugins(mangling)
		self.dictionaries = {}

		self.handlers = dict([(name, handler.initialise(self)) for name, handler in self.__getPlugins(handlers).iteritems()])

	def __getPlugins(self, module):
		return dict([(plugin.name, plugin) for plugin in getPlugins(IConfigPlugin, module)])

	def __iter__(self):
		for server in self.servers.itervalues():
			yield RadiusConfig(server, self)

	def getDictionary(self, location):
		if not self.dictionaries.has_key(location):
			self.dictionaries[location] = RadiusDictionary(location)

		return self.dictionaries[location]

	def getPools(self):
		return self.pools

	def getHandlers(self):
		return self.handlers

	def getAuthenticators(self):
		return self.authenticators

	def getAccountants(self):
		return self.accountants

	def getManglers(self):
		return self.manglers

	def getAuthorisers(self):
		return self.authorisers


class RadiusConfig:
	def __init__(self, config, global_config):
		self.config = config
		self.auth_addr = config.auth_addr
		self.acct_addr = config.acct_addr

		clients = global_config.clients.values() if config.clients is True else [global_config.clients[name] for name in config.clients]
		self.clients = ClientManager(clients)
		self.dictionary = global_config.getDictionary(config.dictionary)

		try:
			handlers = [global_config.handlers[name] for name in config.handlers] # handler order MUST be specified
		except KeyError:
			raise ConfigError, 'Trying to use a handler that does not exist: %s' % name
		self.handlers = HandlerManager(handlers)

	def getClients(self):
		return self.clients	

	def getHandlers(self):
		return self.handlers

	def getDictionary(self):
		return self.dictionary

	def getAuthAddr(self):
		return self.auth_addr

	def getAcctAddr(self):
		return self.acct_addr
