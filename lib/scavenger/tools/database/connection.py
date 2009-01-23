#!/usr/bin/env python
# encoding: utf-8
"""
connection.py

Created by Thomas Mangin on 2008-02-12.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

# datbase wrapper with which commit at the end of a with: block

from __future__ import with_statement

import datetime, time
import threading

# From twisted
def _namedModule(name):
	"""Return a module given its name."""
	topLevel = __import__(name)
	packages = name.split(".")[1:]
	m = topLevel
	for p in packages:
		m = getattr(m, p)
	return m

def dict_factory (cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def adapt_datetime(ts):
	    return time.mktime(ts.timetuple())


# XXX: I do not believe we are catching those exception in our code
class FormatError(Exception):
	pass

# XXX: I do not believe we are catching those exception in our code
class ThreadingError(Exception):
	pass

# 0     Threads may not share the module.
# 1     Threads may share the module, but not connections.
# 2     Threads may share the module and connections.
# 3     Threads may share the module, connections and cursors.

# see: http://www.python.org/dev/peps/pep-0249/

class Connection:
	reconnect = True
	debug=False
	
	def __init__(self, api, debug, *args, **kw):
		self.debug = self.debug or debug
		self.lock = threading.Lock()
		self.api = api
		self.api2 = _namedModule(api)
		if self.api2.threadsafety < 1:
			raise ThreadingError('The module is not thread safe enough')
		self.args=args
		self.kw=kw
		self._connect()
	
	def __del__ (self):
		# need to explicitely delete it from pool
		pass
	
	def _connect (self):
		with self.lock:
			self._connection = self.api2.connect(*self.args, **self.kw)
			try:
				self.api2.register_adapter(datetime.datetime, adapt_datetime)
				self.adapter=True
			except AttributeError:
				# it mean that the module has no register_adapter (sqlite3: yes, MySQLdb: no, pgdb: not looked)
				self.adapter=False
				pass	
			self._connection.row_factory = dict_factory

	def _commit (self):
		with self.lock:
			return self._connection.commit()
	
	def _rollback (self):
		with self.lock:
			return self._connection.rollback()

	def _cursor (self):
		with self.lock:
			return self._connection.cursor()

	def cursor (self):
		return Cursor(self,self.adapter,self.debug)


class Cursor (object):
	debug = False

	def __init__ (self,connection,adapter,debug):
		self.debug = self.debug or debug
		self.adapter = adapter
		self._connection = connection
		self._cursor = None

	def __del__ (self):
		if self._cursor != None:
			self._cursor.close()
	
	def __enter__(self):
		if self.debug: print 'cursor'
		try:
			self._cursor = self._connection._cursor()
			return self
		except:
			if not self._connection.reconnect:
				# XXX: This is probably wrong but I never saw it run
				raise self._connection.api2.DatabaseError()
		self._connection._connect()
		self._cursor = self._connection._cursor()
		return self
	
	def __exit__(self, *args):
		if args == (None,None,None):
			self._connection._commit()
			if self.debug: print 'commit'
		else:
			self._connection._rollback()
			if self.debug: print 'rollback'
		cursor = self._cursor
		self._cursor = None
		cursor.close()
	
	def format (self,query):
		if self.debug:
			if query.count('datetime'):
				raise PortabilityError('datetime is not available under mysql')

		style = self._connection.api2.paramstyle
		if style == 'qmark':
			return query.replace('%s','?').replace('%d','?')
		elif style == 'format':
			return query
		else:
			raise FormatError('can not convert the format')

	def debug_query (self,query,args):
		if self.debug:
			print query.replace('\n',' ').replace('\t',' ').replace('  ',' '), args

	# XXX: Be carefull as we are returning a yield the cursor will not be be destroyed until
	# XXX: The iteration if finished, should avoid this behaviour
	def fetchall(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		if self.adapter:
			for row in self._cursor.fetchall():
				yield row
		else:
			if row is not None:
				for row in self._cursor.fetchall():
					yield dict_factory(self._cursor,row)
			else:
				raise StopIteration()
	
	def fetchone(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		if self.adapter:
			return self._cursor.fetchone()
		row = self._cursor.fetchone()
		if row is not None:
			return dict_factory(self._cursor,row)
		return row
	
	# XXX: Be carefull as we are returning a yield the cursor will not be be destroyed until
	# XXX: The iteration if finished, should avoid this behaviour
	def fetchmany(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		if self.adapter:
			for row in self._cursor.fetchmany():
				yield row
		else:
			if row is not None:
				for row in self._cursor.fetchmany():
					yield dict_factory(self._cursor,row)
			else:
				raise StopIteration()

	def update(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		return self._cursor.rowcount
	
	def insert(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		return self._cursor.lastrowid
		
	def delete(self, query, *args):
		query = self.format(query)
		self.debug_query(query,args)
		self._cursor.execute(query, args)
		return self._cursor.rowcount
	

if __name__ == '__main__':
	connection = Connection('sqlite3',True,'test.sqlite')
	connection.debug = True
#	connection = Connection('pysqlite2.dbapi2','test.sqlite')
	with connection.cursor() as cursor:
		cursor.fetchone('drop table if exists test');
	with connection.cursor() as cursor:
		cursor.fetchone('create table test (a integer)')
		cursor.fetchone('insert into test (a) values (10)')
		for row in cursor.fetchall('select * from test'):
			print row
		cursor.fetchone('insert into test (a) values (20)')
	with connection.cursor() as cursor:
		for row in cursor.fetchall('select * from test;'):
			print row
