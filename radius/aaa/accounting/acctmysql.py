from __future__ import with_statement
from threading import Lock
import types
import MySQLdb

from radius.aaa.connections.accounting import Accounting

class MySQLAccounting(Accounting):
	def initdb(self, **args):
		self.server = args['server']
		self.db = args['db']
		self.user = args['user']
		self.password = args['password']

		insert_table = args['insert_table']
		self.string = "insert into %s (%%s) values (%%s)" % insert_table
		self.log_fields = args['fields']

		self.lock = Lock()
		self.connection = MySQLdb.connect(host=self.server,db=self.db,user=self.user,passwd=self.password)

	def log(self, info):
		keys = []
		qmarks = []
		values = []
		for key, value in self.log_fields.iteritems():
			try:
				value = value % info
			except KeyError:
				continue

			keys.append(key)
			if value.__class__ == types.StringType:
				value = "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"
			values.append(value)

		with self.lock:
			result = self.connection.query(self.string % (','.join(keys), ','.join(values)))
		return True
