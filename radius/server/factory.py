from twisted.internet.protocol import ServerFactory
from twisted.internet.defer import Deferred

from protocol import RadiusServerProtocol

class RadiusAuthServerFactory(ServerFactory):
	protocol = RadiusServerProtocol

	def __init__(self, config, service, schedule):
		self.config = config
		self.service = service
		self.schedule = schedule
		self.handler_manager = config.getHandlers()

	def buildProtocol(self):
		p = self.protocol(self.config)
		p.factory = self
		return p

	def notifyBad(self, *a):
		# XXX: we need proper error handling
		print "+++++++++++++++++++++++++"
		print a
		print "+++++++++++++++++++++++++"

#	# XXX: split this up into a few deferreds
#	def __authenticate(self, packet):
#		handler = self.handler_manager.getAuthenticationHandler(packet)
#		if handler is None:
#			return packet.createRejectResponse()
#
#		response = handler.authenticate() # XXX: should not have to pass the packet - we used it to find the handler
#		p = response.getPacket()
#
#		if response.isAccept():
#			self.service.trackConnection(packet, p)
#			handler = self.handler_manager.getAccountingHandler(p)
#			if handler is not None:
#				handler.account() # XXX: should not have to pass the packet - we used it to find the handler
#
#
#
#		return p
#		
#
#	def dispatch(self, packet):
#		d = Deferred()
#		d.addCallback(self.__authenticate)
#		return d


	def __account(self, response):
		if response.isAccept():
			handler = self.handler_manager.getAccountingHandler(response.getPacket())
			if handler is not None:
				handler.account()

		return response

	def __finish(self, response):
		p = response.getPacket()
		if response.isAccept():
			self.service.trackConnection(p)

		return p

	def dispatch(self, packet):
		d = Deferred()
		d.addCallback(self.handler_manager.getAuthenticationHandler) # returning a handler
		d.addCallback(lambda handler: handler.authenticate()) # returning a response

		# set up a deferred to handle logging without having to wait before we send a response
		a = Deferred()
		a.addCallback(self.__account)
		# we're not interested in the result of schedule but want to return the input we were given - 'response'
		# (func() and False) will evaluate to False and (False or response) gives us our response back.
		d.addCallback(lambda response: (self.schedule(a.callback, response) and False) or response)

		d.addCallback(self.__finish) # returning a radius reponse packet
		return d


class RadiusAcctServerFactory(ServerFactory):
	protocol = RadiusServerProtocol

	def __init__(self, config, service):
		self.config = config
		self.service = service
		self.handler_manager = config.getHandlers()

	def buildProtocol(self):
		p = self.protocol(self.config)
		p.factory = self
		return p

	def dispatch(self, packet):
		handler = self.handler_manager.getAccountingHandler(packet)
		if handler is None:
			return packet.createRejectResponse()

		self.service.trackDisconnection(packet)

		response = handler.account()
		return response.packet


class _RadiusClientFactory(ServerFactory):
	protocol = None

	def __init__(self, config, attributes):
		self.dictionary = config.getDictionary()
		self.clients = config.getClients()
		self.attributes = attributes

	def buildProtocol(self):
		p = self.protocol(self.dictionary)
		p.factory = self
		return p

	def getRequest(self):
		id = self.service.getId()
		authenticator = self.service.getAuthenticator()
		packet = self.packetFactory(id, authenticator, self.attributes)

		return packet

	def notifyResponse(self, packet):
		pass

	def notifyError(self, error):
		pass
