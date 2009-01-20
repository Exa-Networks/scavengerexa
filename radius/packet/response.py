class RadiusResponse:
	def __init__(self, request, response, attributes=None):
		self.request = request
		self.response = response
		self.messages = []
		self.attributes = attributes if attributes is not None else {}

	def isAccept(self):
		return True if self.response is True else False

	def isReject(self):
		return not self.isAccept(self)

	def setAccept(self):
		self.response = True

	def setReject(self):
		self.response = False

	def __repr__(self):
		return "RADIUS response %s %s" % ('ACCEPT' if self.isAccept() else 'REJECT', self.attributes)

	def update(self, other):
		return self.attributes.update(other)

	def log(self, message):
		self.messages.append(message)

	def getPacket(self):
		return self.request.createAcceptResponse(self.attributes) if self.isAccept() else self.request.createRejectResponse()
