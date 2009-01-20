from __future__ import with_statement
import os, types
import struct, socket
from scavenger.tools import ip

class DictionaryError(Exception): pass

attributes = {}
attribute_ids = {}

class StringCodec:
	def encode(self, string):
		return string

	def decode(self, string):
		return string

class IPCodec:
	def encode(self, string):
		return socket.inet_aton(string)

	def decode(self, ip):
		return socket.inet_ntoa(ip)

class IntegerCodec:
	def encode(self, string):
		return struct.pack('!I', int(string))

	def decode(self, string):
		return struct.unpack('!I', string)[0]

class DateCodec:
	def encode(self, string):
		return struct.pack('!I', string)

	def decode(self, string):
		return struct.unpack('!I', string)[0]


class CodecCollection:
	def __init__(self):
		self.codecs = {}
		self.codecs['string'] = StringCodec()
		self.codecs['ipaddr'] = IPCodec()
		self.codecs['integer'] = IntegerCodec()
		self.codecs['date'] = DateCodec()
		self.codecs['octets'] = StringCodec()
	
	def __getitem__(self, item):
		return self.codecs[item]

	def __contains__(self, item):
		return True

codecs = CodecCollection()

class RadiusDictionary:
	VENDOR_SPECIFIC = 26

	def __addAttribute(self, line):
		try:
			_, name, id, type = (v.strip() for v in line.split(None,3))
		except ValueError:
			raise DictionaryError, 'invalid attribute definition: %s' % line

		id = int(id)

		if id == self.VENDOR_SPECIFIC:
			return

		if name in attributes:
			raise DictionaryError, 'attribute %s is defined more than once' % name

		if type not in codecs:
			raise DictionaryError, "attribute %s is of unknown type %s" % (name, type)

		self.attributes[name] = id, type
		self.attribute_ids[id] = name, type

	def __addValue(self, line):
		try:
			_, attribute, name, value = line.split(None, 3)
		except ValueError:
			raise DictionaryError, 'invalid value definition: %s' % line

		# this works but maybe we should 
		value = int(value)

		if not self.values.has_key(attribute):
			self.values[attribute] = {}
		self.values[attribute][name] = value

		# result of this test will (should) always be the result of 'not self.values.has_key(attribute)'
		if not self.value_ids.has_key(attribute):
			self.value_ids[attribute] = {}
		self.value_ids[attribute][value] = name

	def __addVendorAttribute(self, line):
		try:
			_, name, id, type, vendor = line.split(None, 4)
		except ValueError:
			raise DictionaryError, 'invalid attribute definition: %s' % line

		id = int(id)

		if name in attributes:
			raise DictionaryError, 'attribute %s is defined more than once' % name

		if type not in codecs:
			raise DictionaryError, "attribute %s is of unknown type %s" % (name, type)

		vendor_id = self.vendors[vendor]
#		self.vendors[vendor][name] = vendor_id, id, type
		self.vendor_attributes[name] = vendor_id, id, type
		self.vendor_ids[vendor_id][id] = vendor, name, type


	def __addVendor(self, filename):
		vendor, id = None, None
		with open(filename, 'r') as fd:
			for line in fd:
				if line.startswith('VENDOR'):
					_, vendor, id = line.split()
					break

			id = int(id)
			if vendor is None:
				raise DictionaryError, 'dictionary contains no vendor name: %s' % filename

			if vendor in self.vendors:
				raise DictionaryError, 'duplicate vendor name %s in %s' % (vendor, filename)
			self.vendors[vendor] = id

			if id in self.vendor_ids:
				raise DictionaryError, 'duplicate vendor id %d (%s) in %s' % (id, vendor, filename)
			self.vendor_ids[id] = {}


			for line in fd:
				if line.startswith('ATTRIBUTE'):
					self.__addVendorAttribute(line.strip())
				elif line.startswith('VALUE'):
					self.__addValue(line.strip())

	def __getInclude(self, line):
		try:
			include, name = (v.strip() for v in line.split(None,1))
		except ValueError:
			raise DictionaryError, 'invalid include: %s' % line
		
		return name
		
			

	def __init__(self, path):
		self.codecs = CodecCollection()
		self.attributes = {}
		self.attribute_ids = {}
		self.values = {}
		self.value_ids = {}

		self.vendors = {}
		self.vendor_ids = {}
		self.vendor_attributes = {}

		vendor_files = []

		with open(os.path.join(path,'dictionary'), 'r') as fd:
			for line in (l.strip() for l in fd):
				if line.startswith('ATTRIBUTE'):
					self.__addAttribute(line)
				elif line.startswith('VALUE'):
					self.__addValue(line)
				elif line.startswith('$INCLUDE'):
					vendor_file = os.path.join(path, self.__getInclude(line))
					vendor_files.append(vendor_file)

		for vendor_file in (filename for filename in vendor_files if os.path.isfile(filename)):
			self.__addVendor(vendor_file)


	def decode(self, attributes):
		result = {}

		for id, values in attributes.iteritems():
			try:
				name, encoding = self.attribute_ids[id]
			except KeyError:
				vendor, id = id
				vendor, name, encoding = self.vendor_ids[vendor][id]

			res = [self.codecs[encoding].decode(v) for v in values]

			if name in self.values:
				res = [self.value_ids[name][r] for r in res]
			if name not in result:
				result[name] = res
			else:
				result[name].extend(res)

		return result

	def encode(self, attributes):
		result = {}

		for name, values in attributes.iteritems():
			if not hasattr(values, '__iter__'):
				values = [values]

			if name.count(':'):
				name, subname = name.split(':', 1)
				values = ['='.join((subname,value)) for value in values]

			if name in self.values:
				values = [self.values[name][value] for value in values]


			if name in self.attributes:
				id, encoding = self.attributes[name]
			else:
				vendor_id, sub_id, encoding = self.vendor_attributes[name]
				id = vendor_id, sub_id

			if id not in result:
				result[id] = []
				
			result[id].extend([self.codecs[encoding].encode(v) for v in values])

		return result
