from __future__ import with_statement

#
# Copyright 2008 Exa Networks
# This code is placed in the public domain
#

# uses a _lot_ of memory when creating a cdb file with lots of keys
# memory usage can be significantly improved

import struct
import shutil
from StringIO import StringIO

__version__ = 'exa 2.0'

def init (fn):
	return cdb(fn)

def cdbmake (fn,tmp):
	return cdb(fn,tmp).empty()

class error(Exception): pass

class HashSlot:
	def __init__(self, value, position, total):
		self.position = position
		self.value = value
		self.minposition = (self.value /256) % total

	def __cmp__(self, other):
		if self.minposition < other.minposition:
			return -1
		if self.minposition > other.minposition:
			return 1
		return 0

	def __str__(self):
		return ''.join(struct.unpack('ssssssss', struct.pack('<II', self.value, self.position)))

	def __repr__(self):
		return ' '.join((str(v) for v in (self.value, self.position, self.minposition)))


class cdb (dict):
	# compatibility with c cdb code

	def add (self,k,v):
		self[k] = v
	
	def finish (self):
		self.write()

	# end of compatibility

	def __init__(self, filename=None, tmpname=None):
		self.filename = filename
		self.tmpname = tmpname

		if self.filename is None:
			self.fd = StringIO('')
		else:
			self.fd = open(filename, 'r')
		self.debug = False
		self.broken = True
		self.popped = []
		self.newvalues = {}
		self.keep = True

	def empty(self):
		self.keep = False
		self.__clear_ammendments()
		return self

	def __str__ (self):
		s = dict(self.items())
		s.update(self.newvalues)
		return str(s)

	def __repr__ (self):
		s = dict(self.items())
		s.update(self.newvalues)
		return repr(s)

	def __clear_ammendments(self):
		self.popped = []
		self.newvalues = {}

	def __cdbhash(self, key):
		h = 5381 # mmmmagic
		for c in key:
#			h = ((h << 5) + h) ^ ord(c)
			h = (33 * h) ^ ord(c)
		h = h & 0xffffffff
		return h


	def __find_hash_offset(self):
		self.fd.seek(0)
		d = self.fd.read(4)
		if not d.__len__() == 4:
			raise error, 'The specified file is not a valid cdb file'

		d = struct.unpack('<I', struct.pack('ssss', *(b for b in d)))
		return d[0]

	def _read_record(self, pos):
		self.fd.seek(pos)
		kl = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
		dl = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
		key = self.fd.read(kl)
		data = self.fd.read(dl)
		return 8 + kl + dl, key, data

	def update(self, other):
		self.newvalues.update(other)

	def pop(self, item):
		# XXX: should be able to do: if item not in self
		if item not in self.keys():
			raise KeyError, item
		
		if item in self.newvalues:
			res = self.newvalues.pop(item)
		else:
			res = self[item]
		
		self.popped.append(item)
		return res
		

	def __setitem__(self, item, value):
		if item in self.popped:
			self.popped.remove(item)
		self.newvalues[item] = value


	def _get_table(self, item):
		hash = self.__cdbhash(item)
		return hash % 256



	def __getitem__(self, item):
		if item in self.newvalues:
			return self.newvalues[item]

		if item in self.popped:
			raise KeyError, item

		if self.keep is False:
			raise KeyError, item

		hash = self.__cdbhash(item)
		n = hash % 256

		self.fd.seek(8*n)
		hash_pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
		hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

		if hash_len == 0:
			raise KeyError, item

		self.debug = n == 69
		self.debug = False

		slot = (hash/256) % hash_len
#		if self.broken:
#			slot = 0

		if self.debug:
			print item, '\ttable number is', n, '\thash', hash, 'is at byte postion', hash_pos, '\tslot offset is +%s'% slot, 'with', hash_len, 'slots'

		for start, end in (hash_pos+(8*slot), hash_pos + (8*hash_len)), (hash_pos, hash_pos + (8*slot)):
			for seek_pos in xrange(start, end, 8):
				self.fd.seek(seek_pos)
				stored = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
				pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]


				if pos == 0:		# from http://cr.yp.to/cdb/cdb.txt
					if self.debug:
						print "FOUND\tPADDING"
					continue	# "If the byte position is 0, the slot is empty."

				if True or stored == hash:
					len, key, value = self._read_record(pos)
					if self.debug:
						print "FOUND\t", key
					if key == item:
						if self.debug:
							print
							print
						return value
			if self.debug:
				if start <> hash_pos:
					print "CYCLING"


		raise KeyError, item


	def iteritems(self):
		if self.keep is True:
			usefile = True
		else:
			usefile = False

		try:
			end = self.__find_hash_offset() - 2048
		except error:
			usefile = False
		
		if usefile is True:
			read = 0
			while read < end:
				len, key, value = self._read_record(2048+read)
				read += len
				if key in self.popped:
					continue
				if key in self.newvalues:
					continue
				yield key, value

		for key, value in self.newvalues.iteritems():
			yield key, value

	def items(self):
		return [item for item in self.iteritems()]

	def iterkeys(self):
		return (key for key, value in self.iteritems())

	def keys(self):
		return [key for key, value in self.iteritems()]

	def itervalues(self):
		return (value for key, value in self.iteritems())

	def values(self):
		return [value for key, value in self.iteritems()]

	def get(self, item, default=None):
		try:
			value = self[item]
		except KeyError:
			value = default
		return value


	def write(self, filename=None, tmpname=None):
		if filename is None and self.filename is None:
			raise ValueError("nothing to write to")
		filename = filename if filename is not None else self.filename
		tmpname = tmpname if tmpname is not None else self.tmpname
		tmpname = tmpname if tmpname is not None else filename + '.tmp'

		wfd = open(tmpname, 'w')
		tables = {}
		for i in xrange(256):
			tables[i] = []

		wfd.seek(2048)
		written = 0
		for key, value in self.iteritems():
			pos = wfd.tell()
			kl = key.__len__()
			vl = value.__len__()
			key_len = ''.join(struct.unpack('ssss', struct.pack('<I', kl)))
			value_len = ''.join(struct.unpack('ssss', struct.pack('<I', vl)))

			wfd.write(key_len + value_len)
			wfd.write(key)
			wfd.write(value)

			written += kl + vl + 8

			hash = self.__cdbhash(key)
			n = hash % 256

			tables[n].append((hash, pos))


		for i in xrange(256):
			table = tables[i]
			#print i, len(table)
			count = len(table)*2

			hashtable = [HashSlot(hash, pos, count) for hash, pos in table]
			hashtable.sort()

			tables[i] = [wfd.tell(), count]

			written = 0
			extra_slots = []
			p = 0
			mark = None
			for slot in hashtable:
				p += 1
				minpos = slot.minposition
				if minpos > written:
					for j in xrange(minpos - written):
						written += 1

				written += 1
				if written >= count:
					mark = p
					break

			if mark is not None:
				extra_slots = hashtable[p:]
				hashtable = hashtable[:p]


			written = 0
			for slot in hashtable:
				minpos = slot.minposition
				if minpos > written:
					for j in xrange(minpos - written):
						if extra_slots:
							w = extra_slots[0]
							extra_slots = extra_slots[1:]
							wfd.write(str(w))
						else:
							wfd.write('\0\0\0\0\0\0\0\0')
						written +=1
				wfd.write(str(slot))
				written += 1

			for j in xrange(count - written):
				wfd.write('\0\0\0\0\0\0\0\0')
					


		wfd.seek(0)
		for i in xrange(256):
			pos, count = tables[i]
			s = ''.join(struct.unpack('ssssssss', struct.pack('<II', pos, count)))
			wfd.write(s)

		wfd.close()
		shutil.move(tmpname, filename)

		# XXX: bad bad bad
		if filename == self.filename:
			self.__clear_ammendments()
		if self.filename is not None:
			self.fd = open(self.filename, 'r')


class DebugCDB(cdb):
	def _show_sizes(self):
		for table in xrange(256):
	                self.fd.seek(8*table+4)
	                hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

			print table, hash_len

	def _describe_sizes(self):
		sizes = []
		for table in xrange(256):
	                self.fd.seek(8*table+4)
	                hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

			sizes.append((table, hash_len))
		return sizes
					

	def _describe_table(self, table):
		assert 0 <= table < 256

		description = []

                self.fd.seek(8*table)
                hash_pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
                hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

		for slot in xrange(hash_len):
			self.fd.seek(hash_pos+(8*slot))
			stored = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			if pos == 0:
				description.append("EMPTY")
				continue
			len, key, value = self._read_record(pos)
			description.append(key)

		return description

	def _show_table(self, table):
		assert 0 <= table < 256

                self.fd.seek(8*table)
                hash_pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
                hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

		print "table %d is at byte position %s. there are %d slots" % (table, hash_pos, hash_len)
		print

		empty = 0

		for slot in xrange(hash_len):
			self.fd.seek(hash_pos+(8*slot))
			stored = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			if pos == 0:
				empty +=1
				print "EMPTY"
				continue
			len, key, value = self._read_record(pos)
			hash = self.__cdbhash(key)
			print key, ((hash /256) % hash_len)
		print
		print

		print "%d non-empty slots" % (hash_len - empty)
		print
		print


	def _iter_table_keys(self, table):
		assert 0<= table < 256

                self.fd.seek(8*table)
                hash_pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
                hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]


		for slot in xrange(hash_len):
			self.fd.seek(hash_pos+(8*slot))
			stored = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
			if pos == 0:
				continue
			len, key, value = self._read_record(pos)
			yield key

	def _count_passes(self, item):
		if item in self.newvalues:
			return 0

		if item in self.popped:
			raise KeyError, item

		hash = self.__cdbhash(item)
		n = hash % 256

		self.fd.seek(8*n)
		hash_pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
		hash_len = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]

		if hash_len == 0:
			raise KeyError, item

		slot = (hash/256) % hash_len

		count = 0

		start_pos = hash_pos + (8 * slot) # each slot is 8 bytes in size
		end_pos = hash_pos + (8 * hash_len)

		for start, end in ( (start_pos, end_pos), (hash_pos, start_pos) ):
			for seek_pos in xrange(start, end, 8):
				count += 1
				self.fd.seek(seek_pos)
				stored = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]
				pos = struct.unpack('<I', struct.pack('ssss', *(b for b in self.fd.read(4))))[0]


				if pos == 0:		# from http://cr.yp.to/cdb/cdb.txt
					continue	# "If the byte position is 0, the slot is empty."

				if True or stored == hash:
					len, key, value = self._read_record(pos)
					if key == item:
						return count

		raise KeyError, item
		

		


class cdbCursor:
	def __init__(self, filename):
		self.filename = filename

	def __enter__(self):
		return cdb(self.filename)

	def __exit__(self, a,b,c):
		pass

class persistantcdb:
	def __init__(self, filename):
		self.filename = filename

	def getCursor(self):
		return cdbCursor(self.filename)




if __name__ == '__main__':

	c = DebugCDB()
	with open('/usr/share/dict/british-english', 'r') as fd:
		for line in (_line for _line in (l.strip() for l in fd) if _line and _line.isalpha()):
			c[line] = line
			c[2*line] = line
			c[3*line] = line
			c[4*line] = line
			c[5*line] = line
			c[6*line] = line
			c[7*line] = line
			c[8*line] = line
			c[9*line] = line
			c[10*line] = line

	import time
	s = time.time()
	c.write('newtest')
	e = time.time()

	print e - s

	print "***************"
	time.sleep(10)

	c = DebugCDB('newtest')
	d = DebugCDB('newtest.djb')

	for i in xrange(256):
		keys = [k for k in c._describe_table(i) if k <> 'EMPTY']

		c_count = 0
		d_count = 0

		for key in keys:
			c_count += c._count_passes(key)
			d_count += d._count_passes(key)

		if c[key] <> d[key]:
			print ":(", key

		if c_count <> d_count:
			print "table %d" % i
			print "djb took %d passes" % c_count
			print "we took %d passes" % d_count


	import sys
	sys.exit()



	filename = '/home/david/test/test.cdb'

	c = cdb(filename)
	x = {}
	x['hello'] = ':)'
#	for key in c._iter_table_keys(81):
#		c[key]
#
#
#	for key in d._iter_table_keys(81):
#		d[key]

	c.write('test')

	d = cdb('test')
	c['exa-151107-1@dsl.exa-networks.co.uk']
	print
	print
	d['exa-151107-1@dsl.exa-networks.co.uk']



	
	test = ['exa-141105-2@dsl.exa-networks.co.uk', 'exa-230507-1@dsl.exa-networks.co.uk', 'exa-040124-1@dsl.exa-networks.co.uk', 'exa-151107-1@dsl.exa-networks.co.uk', 'exa-161006-2@dsl.exa-networks.co.uk', 'exa-040907-8@dsl.exa-networks.co.uk', 'exa-040507-4@dsl.exa-networks.co.uk', 'exa-050407-4@dsl.exa-networks.co.uk', 'exa-270307-3@dsl.exa-networks.co.uk', 'exa-230606-3@dsl.exa-networks.co.uk', 'exa-210404-1@dsl.exa-networks.co.uk', 'exa-230307-7@dsl.exa-networks.co.uk', 'exa-171105-1@dsl.exa-networks.co.uk']

	for i in xrange(256):
		keys = [k for k in c._describe_table(i) if k <> 'EMPTY']

		c_count = 0
		d_count = 0

		for key in keys:
			c_count += c._count_passes(key)
			d_count += d._count_passes(key)

		if c_count <> d_count:
			print "table %d" % i
			print "djb took %d passes" % c_count
			print "we took %d passes" % d_count
			print


	import sys
	sys.exit()

	for key in c.iterkeys():
		c[key]

	c.write('test')

	d = cdb('test')

	print c._describe_sizes() == d._describe_sizes()
	print

	for i in xrange(254):
		if c._describe_table(i) <> d._describe_table(i):
			print "+++++", i

	c._show_table(16)
	d._show_table(16)
