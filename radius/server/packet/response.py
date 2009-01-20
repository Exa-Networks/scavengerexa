import struct

from stream import AttributeSerialiser
from radius.packet.functions import encrypt_radius_password, decrypt_radius_password



class AttributeStreamFactory:
	def __init__(self, serialiser):
		self.serialiser = serialiser

	def serialise(self, key, value):
		v = str(value)
		length = len(v)
		
		response  = self.serialiser.serialiseInt8(key)
		response += self.serialiser.serialiseInt8(2 + length)
		response += self.serialiser.serialiseString(v, length)
		return response

# XXX: Error checking needed
class VendorFactory:
	def serialise(self, vendor_id, vendor_type, value):
		data  = struct.pack('>I', vendor_id)
		data += chr(vendor_type)
		data += chr(len(value) + 2)
		data += value
		return data


class StreamFactory:
	obfuscation = {'User-Password':encrypt_radius_password}

	def __init__(self, sanitise):
		self.serialiser = AttributeSerialiser()
		self.attribute_factory = AttributeStreamFactory(self.serialiser)
		self.vendor_factory = VendorFactory()
		self.sanitise = sanitise

	def _encode(self, attributes, dictionary, secret, authenticator):
		res = {}
		res.update(attributes)

		for key, m in self.obfuscation.iteritems():
			if key in attributes:
				res[key] = [m(v, secret, authenticator) for v in attributes[key]]
		
		for k in self.sanitise:
			if k in res:
				res.pop(k)

		res = dictionary.encode(res)

		vs = []
		for key in res.keys():
			if isinstance(key, tuple): # Vendor Specific
				for value in res.pop(key):
					vs.append(self.vendor_factory.serialise(*(key + (value,))))
		
		# XXX: make sure that we don't somehow already have an entry for Vendor-Specific
		if vs:
			res[dictionary.VENDOR_SPECIFIC] = vs



		return res

	def serialise(self, packet, dictionary, secret):
		response  = self.serialiser.serialiseInt8(packet.code)
		response += self.serialiser.serialiseInt8(packet.id)

		attributes = self._encode(packet.attributes, dictionary, secret, packet.authenticator)
		attr_string = ''
		for key, values in attributes.iteritems():
			attr_string += ''.join((self.attribute_factory.serialise(key, value) for value in values))
		length = len(attr_string)

		
		response += self.serialiser.serialiseInt16(length+20)
		response += self.serialiser.serialiseString(packet.authenticator, 16)
		response += self.serialiser.serialiseString(attr_string, length)
		return response


