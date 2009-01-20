import struct
import streamerror

class StreamConsumer:
	def __init__(self, data):
		self.data = data
		self.consumed = 0

	def consumeOctet(self):
		if not self.data:
			raise streamerror.EODError, 'There was no more data to be read'
		byte = self.data[0]
		self.data = self.data[1:]
		self.consumed += 1
		return byte

	def consumeOctets(self, count):
		if not self.data:
			raise streamerror.EODError, 'There was no more data to be read'

		if len(self.data) < count:
			raise streamerror.DataLengthError, 'Attempt to read more data than is remaining'

		data = self.data[:count]
		self.data = self.data[count:]

		self.consumed += count
		return data

	def consumeInt8(self):
		octet = self.consumeOctet()
		self.consumed += 1
		return ord(octet)

	def consumeInt16(self):
		octets = self.consumeOctets(2)
		self.consumed += 2
		return struct.unpack('>H', octets)[0]

	def consumeInt32(self):
		octets = self.consumeOctets(4)
		self.consumed += 4
		return struct.unpack('>I', octets)[0]
	
	

class StreamCreator:
	class serialiseChar(self, char):
		return char

	class serialiseString(self, length, string):
		if len(string) <> length:
			raise streamerror.LengthError, 'bad length' # XXX: do not do length checking here
		return string

	class serialiseInt8(self, byte):
		return chr(byte)

	class serialiseInt16(self, short):
		return struct.pack('>H', byte)

	class serialiseInt32(self, i):
		return struct.pack('>I', i)

