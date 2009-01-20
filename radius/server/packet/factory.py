from cStringIO import StringIO
import struct

from stream import StreamConsumer
from definition import known_requests, known_responses
from radius.packet.functions import encrypt_radius_password, decrypt_radius_password

VENDOR_SPECIFIC=26

class AttributeFactory:
        def __init__(self, consumer):
                self.consumer = consumer

	def fromStream(self, stream):
		type = self.consumer.consumeInt8(stream)
		length = self.consumer.consumeInt8(stream)
		if length < 2: # XXX: <= ?
			raise error.CorruptData, 'An attribute cannot have a length of %s' % length
		data = self.consumer.consumeOctets(stream, length-2)
		return length, (type, data)

# XXX: should use a consumer
# should we just take the overhead and create a new stream to pass here?
# XXX: no error checking here atm either
class VendorFactory:
	def fromString(self, data):
		vendor = struct.unpack('>I', data[:4])[0]
		vendor_type = ord(data[4])
		vendor_len = ord(data[5])
		return (vendor, vendor_type), data[6:]


class _PacketFactory:
	attributeFactory = AttributeFactory
	vendorFactory = VendorFactory

	known_packets = None
	# XXX: move obfuscation and single-value elsewhere
	obfuscation = {'User-Password':decrypt_radius_password}

	def __init__(self, dictionary):
		self.dictionary = dictionary
		self.consumer = StreamConsumer()
		self.attribute_factory = self.attributeFactory(self.consumer)
		self.vendor_factory = self.vendorFactory()
		self.packets = dict(((p.code, p) for p in self.known_packets))

	def _decode(self, attributes, secret, authenticator):
		attributes = self.dictionary.decode(attributes)
		for k, m in self.obfuscation.iteritems():
			if k in attributes:
				attributes[k] = [m(v, secret, authenticator) for v in attributes[k]]

		return attributes

	def fromStream(self, data, secret):
		stream = StringIO(data)

		code = self.consumer.consumeInt8(stream)
		identifier = self.consumer.consumeInt8(stream)
		length = self.consumer.consumeInt16(stream)
		authenticator = self.consumer.consumeOctets(stream, 16)


		attributes = {}

		to_read = length - 20
		while to_read > 0:
			_len, (_type, _data) = self.attribute_factory.fromStream(stream)
			to_read -= _len

			if _type == self.dictionary.VENDOR_SPECIFIC:
				_type, _data = self.vendor_factory.fromString(_data)

			if not attributes.has_key(_type):
				attributes[_type] = []
			attributes[_type].append(_data)

		attributes = self._decode(attributes, secret, authenticator)

		if to_read < 0:
			raise error.CorruptData, 'We read %d bytes instead of the declared length of %d' % (length - to_read, length)

		if not self.packets.has_key(code):
			raise error.UnknownRequest, 'code %d is not an acceptable request' % code

		packet = self.packets[code](attributes, identifier, authenticator)
		return packet

class RequestFactory(_PacketFactory):
	known_packets = known_requests

class ResponseFactory(_PacketFactory):
	known_packets = known_responses

#class AuthFactory(PacketFactory):
#	code = 1 # AccessRequest
	

#class AcctFactory(PacketFactory):
#	code = 4 # AccountingRequest
