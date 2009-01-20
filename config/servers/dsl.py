from struct import pack
from socket import htonl

from zope.interface import implements
from twisted.plugin import IPlugin

from radius.config.server import Server


plugin = Server('dsl',
	auth_addr = ('127.0.0.1', 1812),
	acct_addr = ('127.0.0.1', 1813),
#	dictionary = 'default', # has a default
	# XXX: put the correct path here
	dictionary = '/home/david/devel/exa/app/radius/config/dictionaries/', # has a default

	clients = ('dsl', 'office', 'local'), # must be supplied
	handlers = ('dsl',),
)
