from struct import pack,unpack
import struct

from zope.interface import implements
from twisted.plugin import IPlugin
from config import IPoolConfig


class nas_port:
	implements(IPoolConfig)

	def __init__(self, args):
		self.dns = "82.219.4.24 82.219.4.25"
		self.checker = args['checker']
		(self.a, self.b, self.c) = args['ip']

	def logon(self, pkt, attrs):
		if self.checker(pkt):
			attrs[8] = [pack('BBBB', self.a, self.b, self.c, unpack('BBBB',pkt[5][0])[3] + 1)]
		avpair = "ip:dns-servers=%s" % self.dns
		attrs[26] = attrs.get(26, [])
		attrs[26].append(struct.pack("BBBBBB", 0x00,0x00,0x00,0x09,0x01,len(avpair)+2) + avpair)
		return 1

	def logoff(self, pkt):
		pass
