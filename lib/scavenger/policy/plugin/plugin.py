#!/usr/bin/env python
# encoding: utf-8
"""
plugin.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import threading
import random

from zope.interface import Interface, Attribute
from twisted.python import log
from twisted.internet import reactor, defer

from scavenger.tools.database.pool import ConnectionPool, Connection

from zope.interface import implements
from twisted.plugin import IPlugin

def getPlugins (tp,db):
	from twisted.plugin import getPlugins
	from scavenger.policy import plugins
	r = []
	for plugin in getPlugins(ISpamPlugin,plugins):
		database = plugin.getDatabase()
		if tp in plugin.getType() and (database == [] or db in database):
			r.append(plugin)
	return r


class ISpamPlugin (Interface):
	def getName ():
		"""return the name of the plugin"""
	
	def getDatabase():
		"""return the database the plugin will work with"""

	def getConnetionNumber():
		"""return how many connection to the database the plugin would like"""

	def getType ():
		"""return the type of plugin, postfix or scavenger"""

	def getStates ():
		"""return at which states the plugin can be called (first one)"""
	
	def getVersion ():
		"""return what version of the plugin we are running"""

	def requiredAttributes ():
		"""return a list of the non empty attribute the plugin needs from postfix"""
	
	def validateAttributes (message):
		"""return if the message attributes are within expected values"""
	
	def threadSafe ():
		"""return False by default, change it to return True is the plugin is thread safe"""

	def onInitialisation ():
		"""Is called when the plugin is initialised"""
	
	def isTraining ():
		"""is the plugin only gathering data, or is it classifying as well"""
	
	def police (message):
		"""returns what we think of a message"""

	def update (message):
		"""perform any long term storage of information needed even if the test is not performed"""

	def check (message):
		"""return a Exception telling the engine what to do"""

#	initialised = Attribute("""Was the initialise() function been call and successful""")

import response

class PluginDatabase (object):
	debug = True

	database_schema = []
	database_insert = []

	# XXX: we should check if the db (or api) we use is threadsafe to not always lock
	def __init__(self, pool):
		self.pool = pool
		self.api = pool.api
		self.api2 = pool.api2
		self._errors = []

	def _connection (self):
		return self.pool.getConnection()

	# This should be defined at lower level (DB) in case the DB does not know the command
	# sqlite3 and postgresql support vaccum tho
	def vacuum(self):
		self.fetchone('vacuum')

	def __runattr (self, cursor, method, *args, **kwargs):
		with cursor: 
			return method(*args,**kwargs)
	
	def __getattr__ (self,name,*args,**kwargs):
		cursor = self._connection().cursor()
		method = getattr(cursor,name)
		return lambda *args, **kwargs: self.__runattr(cursor, method, *args, **kwargs)

	def create (self):
		errors = []

		try:
			with self._connection().cursor() as cursor:
				for sql in self.database_schema:
					cursor.fetchone(sql)
		except self.api2.OperationalError,e:
			errors.append(str(e))

		try:
			with self._connection().cursor() as cursor:
				for sql in self.database_insert:
					cursor.fetchone(sql)
		except self.api2.OperationalError,e:
			errors.append(str(e))

		return errors	

	def threadSafe (self):
		# SQLITE3 seems to not be happy when multiple write are done at the same time
		# and reports: sqlite3.OperationalError: database is locked

		if self.api == 'sqlite3':
			return False

		# All the modules currently report a thread safety of 1
		# So this always returns False

		# see: http://www.python.org/dev/peps/pep-0249/
		# 0     Threads may not share the module.
		# 1     Threads may share the module, but not connections.
		# 2     Threads may share the module and connections.
		# 3     Threads may share the module, connections and cursors.
		return self.api2.threadsafety >=2


class _SpamPlugin (object):
	implements(IPlugin, ISpamPlugin)

	debug = False
	cleanup_interval = 5*60
	vacuum_interval = 24*60*60
	factory = None
	
	def __init__ (self,name,version):
		self.lock = threading.Lock()
		self.name = name
		self.version = version
		self.database = None
		self.errors = []

	def getDatabase (self):
		return []

	def getConnectionNumber(self):
		return 2

	def threadSafe (self):
		return True

	def initialise (self,service):
		log.msg('initialisation of plugin %s' % self.name)

		self.service = service
		# XXX: Intercept issue with finding configuration
		if self.debug: log.msg('  * reading configuration file')
		self.configuration = service.getConfiguration(self.name)

		if self.debug: log.msg('  * running plugin initialisation')
		if not self._initialise ():
			log.msg('  - failure to initialiase ')
			return False
		else:
			if self.debug: log.msg('  * complete')
			return True
	
	def _initialise (self):
		if self.configuration.get('disable',False):
			self.errors = ['The plugin is disabled in the configuration',]
			return False

		if not self._databaseConnection():
			if self.debug: log.msg('  * initialisation of the database')
			self.errors = ['could not initialise the database',] + self.errors
			return False

		try:
			return self.onInitialisation()
		except (TypeError, ValueError, KeyError), e: # XXX: this is probably very bad
			self.errors = ['could not initialise the plugin',e.message] +self.errors
			self.errors.append(e.message)
			return False
	
	def onInitialisation (self):
		return True
	
	def _databaseConnection (self):
		if not self.factory:
			return True

		api = self.configuration['dbapi']
		connections = self.getConnectionNumber()

		conf = {}
		db = "%s_%s%d" % (self.configuration['database_prefix'],self.getName(),self.getVersion())
		if api in ['MySQLdb','pgdb']:
			conf['host'] = self.configuration['database_host']
			conf['port'] = self.configuration['database_port']
			conf['user'] = self.configuration['database_user']
			conf['passwd'] = self.configuration['database_password']
			conf['db'] = ''

			connection = Connection(api,self.factory.debug,**conf)
			try:
				with connection.cursor() as cursor:
					cursor.fetchone('create database %s' % db)
				log.msg('    = creating database for plugin')
			except connection.api2.ProgrammingError:
				# the database already exists
				pass

			conf['db'] = db
			pool = ConnectionPool(api,connections,self.factory.debug,**conf)
		else:
			file = os.path.join(os.path.abspath(self.configuration['database_path']),db)
			pool = ConnectionPool(api,connections,self.factory.debug,file)

		self.database = self.factory(pool)
		self.errors += self.database.create()
		return self.errors == []
	
	def getName (self):
		return self.name
	
	def getVersion (self):
		return 1
	
	def getStates (self):
		return self.configuration.get('states',['DATA',])

	def requiredAttributes (self):
		return []

	def validateAttributes (self,message):
		return True

	def isTraining (self):
		return False

	def store (self,message):
		if not self._messageContains(message,self.requiredAttributes()):
			return response.DataError('the message is missing needed attribute for the plugin')
		if not self.validateAttributes(message):
			return response.DataError('the message is values are invalid for the plugin')

		return self._wrap(self.update,message)

	def police (self,message):
		if self.isTraining():
			return response.ResponseContinue
		return self._wrap(self.check,message)

	def _wrap (self,function,message):
		if self.factory is not None:
			return self._wrap_database(function,message)
		return self._wrap_simple(function,message)
	
	def _wrap_simple (self,function,message):
		if self.threadSafe():
			return function(message)
		with self.lock:
			return function(message)

	def _wrap_database (self,function,message):
		try:
			if self.threadSafe() and self.database.threadSafe():
				return function(message)
			with self.lock:
				return function(message)
		except self.database.api2.OperationalError, e:
			return response.InternalError, e.message

	def periodic_cleanup(self):
		log.msg('calling cleanup for %s' % self.getName())
		reactor.callLater(self.cleanup_interval, self.periodic_cleanup)
		self._wrap(self._cleanup,None)

	def _cleanup(self,_):
		return self.cleanup()
		
	def update(self,message):
		return

	def cleanup(self):
		return True

	def _vacuum(self):
		log.msg('vacuuming db for %s' % self.getName())
		self.vacuum()
		reactor.callLater(self.vacuum_interval + random.randint(0, 1), self._vacuum)

	def vacuum(self):
		if self.database is None:
			return True

		with self.lock:
			self.database.vacuum()

		return True


	def _messageContains (self,message,keys):
		for key in keys:
			if message.get(key,'') == '':
				log.msg('plugin %s, message does not have attribute %s set' % (self.name,key))
				return False
		return True


class MultiPlugin (_SpamPlugin):
	def getType (self):
		return []


class PostfixPlugin (_SpamPlugin):
	def getType (self):
		return ["postfix",]


class ScavengerPlugin (_SpamPlugin):
	def getType (self):
		return ["scavenger",]
