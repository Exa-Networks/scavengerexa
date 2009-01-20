from struct import pack
from socket import htonl

from zope.interface import implements
from twisted.plugin import IPlugin
from config import IHandlerConfig

from radius.config.handler import Handler


plugin = Handler('default',
	auth = 'reject'
)
