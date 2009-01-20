from __future__ import with_statement
from radius.aaa.connections.accounting import Accounting

import MySQLdb

import types
class OmniDict(types.DictType):
	def __getitem__(self, item):
		return types.DictType.get(self, item, None)

class MySQLAccounting(Accounting):
	def initdb(self, **args):
		self.server = args['server']
		self.db = args['db']
		self.user = args['user']
		self.password = args['password']

		insert_table = args['insert_table']
		self.string = "insert into %s (%%s) values (%%s)" % insert_table
		self.log_fields = args['fields']
		self.connection = MySQLdb.connect(host=self.server,db=self.db,user=self.user,passwd=self.password)
		print dir(self.connection.cursor())

	def log(self, info):
		keys = []
		qmarks = []
		values = []
		_info = OmniDict(info)
		for key, value in self.log_fields.iteritems():
			value = value % _info
			if value is None:
				continue
			keys.append(key)
			qmarks.append('?')
			values.append(value)

		result = self.connection.cursor().execute(self.string % (','.join(keys), ','.join(qmarks)), *values)
		return True
