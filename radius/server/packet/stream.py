import struct
import streamerror

class StreamConsumer:
	def __init__(self):
		self.consumed = 0

	def consumeOctet(self, data):
		consumed = data.read(1)
		if not consumed:
			raise streamerror.EODError, 'There was no more data to be read'

		self.consumed += 1
		return consumed

	def consumeOctets(self, data, count):
		consumed = data.read(count)
		if len(consumed) < count:
			raise streamerror.DataLengthError, 'Attempt to read more data than is remaining'

		self.consumed += count			
		return consumed

	def consumeInt8(self, data):
		octet = self.consumeOctet(data)
		return ord(octet)

	def consumeInt16(self, data):
		octets = self.consumeOctets(data, 2)
		return struct.unpack('>H', octets)[0]

	def consumeInt32(self, data):
		octets = self.consumeOctets(data, 4)
		return struct.unpack('>I', octets)[0]
	
	

class AttributeSerialiser:
	def serialiseChar(self, char):
		return char

	def serialiseString(self, string, length):
		if len(string) <> length:
			raise streamerror.LengthError, 'bad length' # XXX: do not do length checking here
		return string

	def serialiseInt8(self, byte):
		return chr(byte)

	def serialiseInt16(self, short):
		return struct.pack('>H', short)

	def serialiseInt32(self, i):
		return struct.pack('>I', i)

