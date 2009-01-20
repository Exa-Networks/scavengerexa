import md5
import response

class _Packet:
	serialFactory = response.StreamFactory
	name = None
	code = None
	ack = None
	nack = None

	multivalue = ('Vendor-Specific',)
	sanitise = ('User-Password', 'CHAP-Password', 'CHAP-Challenge')

	def __init__(self, attributes, id, authenticator):
		self.id = id
		self.authenticator = authenticator
		self.attributes = attributes
		self._serial_factory = self.serialFactory(self.sanitise)

	def serialise(self, dictionary, secret):
		return self._serial_factory.serialise(self, dictionary, secret)

	def __str__(self):
		return '%s (code %d)\nid %d\nauthenticator %s' % (self.name, self.code, self.id, self.authenticator.encode('hex'))

	def __getitem__(self, item):
		if item in self.multivalue:
			return self.attributes.__getitem__(item)
		return self.attributes.__getitem__(item)[0]

	def get(self, item, default=None):
		if item in self.multivalue:
			return self.attributes.get(item, default)
		return self.attributes.get(item, [default])[0]

		

#	def __setitem__(self, item, value):
#		return self.attributes.__setitem__(self, item, value)

#	def __iter__(self):
#		return self.attributes.__iter__()
#
#	def items(self):
#		return self.attributes.items()
#
#	def keys(self):
#		return self.attributes.keys()
#
#	def values(self):
#		return self.attributes.values()
#
#	def iteritems(self):
#		return self.attributes.iteritems()
#
#	def iterkeys(self):
#		return self.attributes.iterkeys()
#
#	def itervalues(self):
#		return self.attributes.itervalues()
#
#	def get(self, key, default=None):
#		return self.attributes.get(key, default)
#
#	def pop(self):
#		return self.attributes.pop()
#
#	def popitem(self):
#		return self.attributes.popitem()
#
#	def update(self):
#		return self.attributes.update()
#
#	def clear(self):
#		return self.attributes.clear()

	def has_key(self, key):
		return self.attributes.has_key(key)

	



class _ResponsePacket(_Packet):
	def __init__(self, attributes, id, authenticator):
		_Packet.__init__(self, attributes, id, authenticator)

		# XXX: generate these values properly
		self.authenticator_offset = 4
		self.attribute_offset = 20

	def serialise(self, dictionary, secret):
		serialised = self._serial_factory.serialise(self, dictionary, secret)
		authenticator = md5.new(serialised+secret).digest()
		return serialised[:self.authenticator_offset] + authenticator + serialised[self.attribute_offset:]
		



class AccessAccept(_ResponsePacket):
	name = 'Access-Accept'
	code = 2

class AccessReject(_ResponsePacket):
	name = 'Access-Reject'
	code = 3

class AccountingResponse(_ResponsePacket):
	name = 'Accounting-Response'
	code = 5

class DisconnectAccept(_ResponsePacket):
	name = 'Disconnect-Accept'
	code = 41

class DisconnectReject(_ResponsePacket):
	name = 'Disconnect-Reject'
	code = 42

class COAAccept(_ResponsePacket):
	name = 'COA-Accept'
	code = 44

class COAReject(_ResponsePacket):
	name = 'COA-Reject'
	code = 45









class _RequestPacket(_Packet):
	duplicate_attributes = ('NAS-IP-Address', 'NAS-Port-Id', 'Framed-Protocol', 'Service-Type', 'NAS-Port-Type', 'NAS-Port')

	def __init__(self, attributes, id=None, authenticator=None):
		id = id if id is not None else self._generateID()
		authenticator = authenticator if authenticator is not None else self._generateAuthenticator()
		_Packet.__init__(self, attributes, id, authenticator)

	def _generateID(self):
		return random.randint(0,255)

	def _generateAuthenticator(self):
		return struct.pack('IIII', *(random.randint(0, 0xffffffff) for i in xrange(4)))

	def createResponse(self, ack, attributes):
		factory = self.ack if ack is True else self.nak
		attr = {}
		attr.update(dict(((k,v) for k,v in self.attributes.iteritems() if k in self.duplicate_attributes)))
		attr.update(attributes)
		return factory(attr, self.id, self.authenticator)





class AccessRequest(_RequestPacket):
	name = 'Access-Request'
#	responseFactory = response.authResponseFactory
	serialFactory = response.StreamFactory
	code = 1 # Access-Request
	ack = AccessAccept
	nak = AccessReject

	def createAcceptResponse(self, attributes=None):
		# XXX FIXME: we need to sanitise the attributes
		return self.createResponse(True, attributes if attributes is not None else self.attributes)

	def createRejectResponse(self):
		return self.createResponse(False, {})

	


class AccountingRequest(_RequestPacket):
	name = 'Accounting-Request'
	#responseFactory = response.acctResponseFactory
	serialFactory = response.StreamFactory
	code = 4 # Accounting-Request
	ack = AccountingResponse
	nack = None

	def createResponse(self, attributes):
		return _requestPacket.createResponse(True, attributes)

	


class DisconnectRequest(_RequestPacket):
	name = 'Disconnect-Request'
	#responseFactory = response.disconnectResponseFactory
	serialFactory = response.StreamFactory
	code = 40
	ack = DisconnectAccept
	nak = DisconnectReject

	def createAcceptResponse(self):
		return self.createResponse(True, {})

	def createRejectResponse(self):
		return self.createResponse(False, {})




class COARequest(_RequestPacket):
	name = 'COA-Request'
	#responseFactory = response.COAResponseFactory
	serialFactory = response.StreamFactory
	code = 43
	ack = COAAccept
	nak = COAReject

	def createAcceptResponse(self):
		return self.createResponse(True, {})

	def createRejectResponse(self):
		return self.createResponse(False, {})




known_requests = [AccessRequest, AccountingRequest, DisconnectRequest, COARequest]
known_responses = [AccessAccept, AccessReject, AccountingResponse, DisconnectAccept, DisconnectReject, COAAccept, COAReject]
