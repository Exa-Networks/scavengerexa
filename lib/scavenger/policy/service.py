#!/usr/bin/env python
# encoding: utf-8
"""
service.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import thread

from zope.interface import Interface, implements

class IMailPolicyService (Interface):
	def getConfiguration (name):
		"""returns a copy of the configuration settings"""
	
	def getPlugins ():
		"""return a list to the registered anti-spam plugins"""

	def getType ():
		"""return the type of policy we are"""

from twisted.python import log
from twisted.application import service
from twisted.internet import defer

from scavenger.policy.plugin.plugin import getPlugins
from scavenger.policy.configuration import Configuration,ConfigurationError

from twisted.internet import reactor

class PluginError (Exception):
	pass

class MailPolicyService (service.Service):
	implements (IMailPolicyService)
	
	def __init__(self,configuration):
		log.msg("*"*80)
		
		self.ready = False
		self.configuration_lock = thread.allocate_lock()
		self.configuration = configuration
		self.type = self.configuration['type']
		
		if self.type not in ['postfix','scavenger']:
			raise PluginError('Trying to act for an unknown type of plugin %s' % self.type)

		self.registered = self.configuration['plugins']

		api = self.configuration.get('api','sqlite3')
		if api == 'sqlite3':
			try:
				# python 2.5
				import sqlite3 as sql
				self.configuration['dbapi'] = api
			except:
				# try alternative
				self.configuration['dbapi'] = 'pysqlite2.dbapi2'
		elif api == 'mysql':
			self.configuration['dbapi'] = 'MySQLdb'
		elif api == 'postgresql':
			self.configuration['dbapi'] = 'pgdb'
		else:
			raise PluginError('Invalid database type: %s' % api)

		plugins = getPlugins(self.type,api)
		if len(plugins) == 0:
			raise PluginError('Can not find any plugin')
		
		skipped = []
		failed = []
		error = {}
		self.plugins = {}
		for plugin in plugins:
			if plugin.name not in self.registered:
				skipped.append(plugin)
				continue
			if plugin.initialise(self):
				self.plugins[plugin.getName()] = plugin
			else:
				failed.append(plugin)
		
		unloaded = []
		#print "self.plugin.keys", self.plugins.keys()
		#print "self.registered", self.registered
		for name in self.registered:
			if name not in self.plugins.keys():
				unloaded.append(name)

		if unloaded:
			log.msg('-'*80)
			log.msg('plugin not loaded %s' % ", ".join(unloaded))

		for f in failed:
			log.msg('')
			log.msg('failure to load plugin %s' % f.getName())
			for error in f.errors:
				log.msg('    - ' + str(error))
		
		if skipped: log.msg('-'*80)
		for s in skipped:
			log.msg('skipping uncalled plugin %s' % s.getName())
		
		self.cleanupPlugins()


	def cleanupPlugins(self):
		for name, plugin in self.plugins.iteritems():
			try:
				plugin.periodic_cleanup()
			except:
				log.msg('error while trying to cleanup plugin ' + name)

			try:
				reactor.callLater(plugin.vacuum_interval, plugin._vacuum)
			except:
				log.msg('error while trying to vacuum plugin ' + name)
				
		
	def getConfiguration (self,name):
		with self.configuration_lock:
			generic = self.configuration.copy()
			configuration = Configuration(os.path.join(self.type,name+'.conf'))
			generic.update(configuration)
			return generic
			
	def getPlugins (self):
		for name in self.registered:
			if name in self.plugins:
				yield self.plugins[name]
	
	def getType (self):
		return self.type
			
