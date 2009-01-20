import types

from radius.packet.response import RadiusResponse

class ManagedHandler:
	def __init__(self, handler, packet):
		self.handler = handler
		#self.packet = handler.rewriteRequest(packet)
		self.packet = packet

	def authenticate(self):
		return self.handler.authenticate(self.packet)

	def account(self):
		return self.handler.account(self.packet)

	
# XXX: put this in a better place
# this is a special case returned only by a handlermanager so we can
# just behave like a managedhandler
class NullHandler:
	def __init__(self, packet):
		self.packet = packet

	def authenticate(self):
		return RadiusResponse(self.packet, False)

	def account(self):
		return None

class HandlerManager:
	def __init__(self, handlers=None):
		self.authentication = []
		self.accounting = []
		if handlers is not None:
			for handler in handlers:
				self.addHandler(handler)

	def addHandler(self, handler):
		if handler.auth is not None:
			self.authentication.append(handler)
		if handler.acct is not None:
			self.accounting.append(handler)

	def getAuthenticationHandler(self, packet):
		for handler in self.authentication:
			if handler.matches(packet):
				return ManagedHandler(handler, packet)

		return NullHandler(packet)

	def getAccountingHandler(self, packet):
		for handler in self.accounting:
			if handler.matches(packet):
				return ManagedHandler(handler, packet)

		return NullHandler(packet)



class ClientManager:
	def __init__(self, clients=[]):
		self.clients = clients[:]

	def addClient(self, client):
		self.clients.append(client)

	def find(self, host, port):
		for client in self.clients:
			if client.addr == host:
				return client
