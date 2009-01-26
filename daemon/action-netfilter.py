#!/usr/bin/env python
# encoding: utf-8
"""
action-netfilter.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import sys
import time
import threading

try:
	from netfilter.table import Table,IptablesError
	from netfilter.rule import Rule,Match,Target
except ImportError:
	print "this program require python-netfilter http://opensource.bolloretelecom.eu/projects/python-netfilter/"
	sys.exit(1)

import os
from scavenger.action.option import Option as BaseOption, OptionError

class Option (BaseOption):
	valid = ['debug','slow','port','timeout', 'database','mta','ports','table','chain','jump', ]

	def _database (self):
		self['database'] = self._env('database')

	def _mta (self):
		self['mta'] = self._validate_service(self._env('mta'))

	def _ports (self):
		self['ports'] = self._env('ports')
		if not self['ports']:
			self['ports'] = '25 587'
		self['ports'] = [port for port in  self['ports'].split(' ') if port]
		for port in self['ports']:
			if not port.isdigit():
				raise OptionError('port is not an integer')
			if int(port) >= 65536:
				raise OptionError('port is too big %s' % port)

	# Those are options but should not be changed unless you really know what you are doing ...

	def _table (self):
		self['table'] = self._env('table')
		if not self['table']:
			self['table'] = 'nat'

	def _chain (self):
		self['chain'] = self._env('chain')
		if not self['chain']:
			self['chain'] = 'PREROUTING'

	def _jump (self):
		self['jump'] = self._env('jump')
		if not self['jump']:
			self['jump'] = 'DNAT'


try:
	option = Option()
except OptionError, e:
	print str(e)
	sys.exit(1)

# Enabling (or not) psycho

if not option['slow']:
	try:
		import psyco
		psyco.full()
		print 'Psyco found and enabled'
	except ImportError:
		print 'Psyco is not available'

# Debugging

debug_option = not not option.debug & 1
debug_cleanup = not not option.debug & 2
debug_database = not not option.debug & 4

if debug_option:
	option.display()
	print "debug cleanup ", debug_cleanup
	print "debug database", debug_database
	print "+"*80

if debug_cleanup:
	cleanup_time=5
else:
	cleanup_time=60

# setup/check of netfilter

try:
	_table = Table(option['table'])
	if option['chain'] not in _table.list_chains():
		print 'can not find the chain name provided:', option['chain']
		sys.exit(1)
except IptablesError,e:
	print 'can not find the table specified:', option['table']
	sys.exit(1)

# connection to database

from scavenger.tools.database.connection import Connection

class Database (object):
	_create = """
create table if not exists tracking
(
	start		integer,
	end		integer,
	expiration	integer default 0,
	message		varchar default '',

	primary key (start,end)
)
		 """.strip()

	_insert = """
insert into tracking (start,end,expiration,message) values (?,?,?,?)
		""".strip()
	
	_expire = """
select expiration from tracking where start = ? and end = ?
		""".strip()
	
	_delete = """
delete from tracking where start = ? and end = ?
		""".strip()
	

	def __init__ (self,debug,location):
		self.connection = Connection('sqlite3',debug,location)
		
		with self.connection.cursor() as cursor:
			cursor.fetchone(self._create)

	def expire (self,start,end):
		with self.connection.cursor() as cursor:
			r = cursor.fetchone(self._expire,start,end)
		
			if r is None:
				return False
			expiration = long(r['expiration'])
			now = long(time.time())

			if now < expiration:
				return False

			r = cursor.fetchone(self._delete,start,end)
			return True
	
	def delete (self,start,end):
		with self.connection.cursor() as cursor:
			cursor.fetchone(self._delete,start,end)
	
	def insert (self,start,end,duration,message):
		expiration = long(time.time()) + duration
		with self.connection.cursor() as cursor:
			try:
				r = cursor.fetchone(self._insert,start,end,expiration,message)
			except self.connection.api2.IntegrityError:
				# not unique, just report it but do nothing (should not happen)
				print 'trying to insert non-unique record for %d-%d,%d' % (start,end,duration)


#d = Database(True,option['database'])
#print "insert %s" % str(d.insert(0,0,2))
#print "expire %s" % str(d.expire(0,0))
#time.sleep(2)
#print "expire %s" % str(d.expire(0,0))
#sys.exit(0)

# Protocol

from scavenger.tools.ip import tobits,toslash,tosize,toips,toipn
from scavenger.action.protocol import ActionProtocol

class MailProtocol (ActionProtocol):
	def run (self,ip,action,destination,duration,message):
		if destination == '0.0.0.0:00000':
			destination = '%s:%d' % option['mta']
		if action != 'FILTER':
			print 'only filter is implemented'
		else:
			self.factory.addFilter(toipn(ip),toipn(ip),destination,duration,message)

# Factory

from twisted.internet import protocol
from twisted.internet import reactor

class MailFactory (protocol.Factory):
	protocol = MailProtocol
	debug = False

	def __init__ (self):
		self.database = Database(debug_database,option['database'])
		self.lock = threading.Lock()
		self.table = _table
		self.rules = self._getFilters(option)
		self._reArm()

	def _reArm (self):
		reactor.callLater(cleanup_time,self._cleanup,None)
	
	def _getFilters(self,option):
		rules = {}
		for rule in self.table.list_rules(option['chain']):
			if rule.protocol != 'tcp':
				continue
			if rule.destination is not None:
				continue
			if len(rule.matches) != 1:
				continue
			opts = rule.matches[0].options()
			if 'dport' not in opts:
				continue
			found = False
			for opt in opts['dport']:
				if option['ports'].count(opt):
					found = True
			if not found:
				continue
			if rule.jump.name() != option['jump']:
				continue
			opts = rule.jump.options()
			if 'to-destination' not in opts:
				continue

			parts = rule.source.split('/',1)
			parts = parts + ['255.255.255.255']
			ip = parts[0]
			netmask = parts[1]

			try:
				first = toipn(ip)
				first = 0L + toipn(ip)
				last = 0L + first + tosize(toslash(netmask)) - 1
			except (KeyError,ValueError,IndexError):
				# XXX: I am surely missing another error which can be raised
				# XXX: But as the data comes from a 'trusted' source it should not happen
				# invalid ip/netmask
				continue
			rules[(first,last)] = rule
		return rules

	def addFilter (self,start,end,destination,duration,message):
		if debug_cleanup:
			duration = 10
		with self.lock:
			ip = toips(start)
			l = end-start+1
			slash = tobits(l)

			for s,e in self.rules:
				if start>=s and start<=e:
					print 'overlapping rule ignored (start) %s/%d' % (ip,slash)
					return
				if end>=s and end<=e:
					print 'overlapping rule ignored (end) %s/%d' % (ip,slash)
					return

			rule = Rule(
				protocol='tcp',
				source='%s/%d' % (ip,slash),
				matches=[Match('tcp','--destination-port 587')],
				jump=Target(option['jump'],'--to-destination %s' % destination))
			if not self.debug:
				self.table.append_rule(option['chain'], rule)
			self.database.insert(start,end,duration,message)
			self.rules[(start,end)] = rule
			print "added %s/%d" % (ip,slash)
	
	def delRule (self,start,end):
		with self.lock:
			delete = []
			now = int(time.time())
			for s,e in self.rules:
				if s == start and e == end:
					delete.append((s,e))
			for s,e in delete:
				rule = self.rules[(s,e)]
				self.table.delete_rule(option['chain'],rule)
				del self.rules[(s,e)]
				self.database.delete(start,end)
				print 'deleted rule %s/%d' % (toips(start),tobits(end-start+1))


	def _cleanup (self,_):
		if debug_cleanup: print 'cleanup'
		self._reArm()

		with self.lock:
			delete = []
			for start,end in self.rules:
				rule = self.rules[(start,end)]
				if self.database.expire(start,end):
					delete.append((start,end))

			for start,end in delete:
				self.table.delete_rule(option['chain'],rule)
				del self.rules[(start,end)]
				print 'expired rule %s/%d' % (toips(start),tobits(end-start+1))

# Starting ...

from twisted.application import internet, service
from twisted.protocols import policies

application = service.Application('action-netfilter')
serviceCollection = service.IServiceCollection(application)

factory = policies.TimeoutFactory(MailFactory(),timeoutPeriod=option.timeout)
internet.TCPServer(option.port, factory).setServiceParent(serviceCollection)

serviceCollection.startService()
reactor.run()
sys.exit(1)


