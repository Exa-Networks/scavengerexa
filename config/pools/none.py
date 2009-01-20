from struct import pack,unpack
from socket import htonl
from string import atoi
import struct
import _mysql
import ldap

from zope.interface import implements
from twisted.plugin import IPlugin
from config import IPoolConfig


class none:
	implements(IPoolConfig)

	def __init__(self, args):
		pass

	def logon(self, pkt, attrs):
		return 1
	
	def logoff(self, pkt):
		pass

