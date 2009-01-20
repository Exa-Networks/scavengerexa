from __future__ import with_statement
from radius.aaa.connections.authentication import Authentication

from scavenger.tools import cdb

class CDBAuthentication(Authentication):
	def initdb(self, **args):
		self.format = args['format']
		self.delimiter = args['delimiter']
		self.search_key = args['search_key']
		cdbfile = args['cdbfile']
		self.connection = cdb.persistantcdb(cdbfile)

	def search(self, request):
		key = self.search_key % request
		with self.connection.getCursor() as cursor:
			result = cursor.get(key, None)

		if result is None:
			return None

		result = result.split(self.delimiter)
		return dict(zip(self.format, result))

