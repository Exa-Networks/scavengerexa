from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from packet.factory import RequestFactory


class RadiusServerProtocol(DatagramProtocol):
	packetFactory = RequestFactory

	def __init__(self, config):
		self.clients = config.getClients()
		self.dictionary = config.getDictionary()
		self._factory = self.packetFactory(self.dictionary)

	def datagramReceived(self, data, (host, port)):
		client = self.clients.find(host, port)
		if client is None:
			return None

		packet = self._factory.fromStream(data, client.secret)
		d = self.factory.dispatch(packet)
		d.addCallback(lambda r: r.serialise(self.dictionary, client.secret)) # XXX: do this without having to pass dictionary
		d.addCallback(self.transport.write, (host, port))
		
		reactor.suggestThreadPoolSize(50)
		reactor.callInThread(d.callback, packet)




#class RadiusAuthServerProtocol:
#	packetFactory = packet.AuthFactory

#class RadiusAcctServerProtocol:
#	packetFactory = packet.AcctFactory


class _RadiusClientProtocol(DatagramProtocol):
	responseFactory = None

	def __init__(self, config):
		self.secret = config.getSecret() # XXX
		self._factory = self.responseFactory()

	def connectionMade(self):
		self.transport.write(self.factory.getRequest().serialise(self.secret))

	def datagramReceived(self, data, (host, port)):
		packet = self._factory(data, self.secret)
		d = self.factory.notifyResponse(packet)


#class RadiusDisconnectClientProtocol(_RadiusClientProtocol):
#	responseFactory = packet.DisconnectResponseFactory
#
#class RadiusCOAClientProtocol(_RadiusClientProtocol):
#	responseFactory = packet.COAResponseFactory
#
#class RadiusAuthClientProtocol(_RadiusClientProtocol):
#	responseFactory = packet.AuthResponseFactory
#
#class RadiusAcctClientProtocol(_RadiusClientProtocol):
#	responseFactory = packet.AcctResponseFactory
