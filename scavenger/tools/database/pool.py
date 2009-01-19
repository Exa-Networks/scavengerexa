#!/usr/bin/env python
# encoding: utf-8
"""
pool.py

Created by Thomas Mangin on 2008-02-12.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import threading
from scavenger.tools.database.connection import Connection, _namedModule

class ConnectionInUseError (Exception):
	pass

class PoolConnection (Connection):
	debug = False
	def __init__ (self,pool,debug,*args,**kw):
		self.debug = self.debug or debug
		self.pool = pool
		self.active = False
		Connection.__init__(self,pool.api,self.debug,*args,**kw)

	def __del__ (self):
		if not self.pool.returnsConnection(self):
			Connection.__del__(self)
	
	def __enter__ (self):
		if self.active:
			raise ConnectionInUseError('This database connection is already in use')
		self.active = True
		Connection.__enter__(self)
		return self
		
	def __exit__ (self,*args,**kw):
		Connection.__exit__(self,*args,**kw)
		self.active = False

class ConnectionPool:
	ARGS = ['number','reconnect']
	number = 10
	reconnect = True
	debug = False
	
	def __init__ (self,api,number,debug,*args,**kw):
		self.running = False
		self.api = api
		self.number = number
		self.debug = self.debug or debug

		self.args = args
		self.kw = kw
		self.api2 = _namedModule(self.api)

		self.connections = []

		self.lock = threading.Lock()
		self.semaphore = threading.Semaphore(self.number)
		
		for i in range(self.number):
			self.connections.append(self._getConnection())
		
		self.running = True

	def _getConnection (self):
		return PoolConnection(self,self.debug,*self.args,**self.kw)

	def stop (self):
		with self.lock:
			self.running = False
	
	def __del__ (self):
		self.stop()
	
	def getConnection (self):
		if self.debug: print 'connection wanted'
		with self.lock:
			if len(self.connections) == 0:
				print 'creating new db connection'
				return self._getConnection()
			if self.debug: print 'remaining %d/%d' % (len(self.connections) -1,self.number)
			connection = self.connections.pop()
			return connection
	
	def returnsConnection (self,connection):
		with self.lock:
			if self.running:
				if len(self.connections) == self.number:
					print 'dropping extra connection'
					return False
				self.connections.append(connection)
		if self.debug: print 'available %d/%d' % (len(self.connections),self.number)
		return self.running

__all__ = ['ConnectionPool',]

if __name__ == '__main__':
	pool = ConnectionPool('sqlite3',5,'/tmp/test.sql')
	connection = pool.getConnection()
	with connection.cursor() as cursor:
		cursor.fetchall('create table test1 (a integer)')
	
	connection1 = pool.getConnection()

	with pool.getConnection().cursor() as cursor:
		cursor.fetchall('create table test2 (a integer)')
	
	connection2 = pool.getConnection()
	
	with pool.getConnection().cursor() as cursor:
		cursor.fetchall('create table test3 (a integer)')

	del (connection1)
	del (connection2)
	
	for i in range(10):
		with pool.getConnection().cursor() as cursor:
			cursor.fetchall('create table t%s (a integer)' % str(i))
