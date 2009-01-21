#!/usr/bin/env python
# encoding: utf-8
"""
grey.py

Created by Thomas Mangin on 2008-02-28.
Modified by David Farrar on 2008-03-07
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement
import types
import time

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import PluginDatabase
from scavenger.policy.plugin import response

from twisted.python import log

tables = {
	'table_whitelist':    'whitelist',
	'table_tracking':     'tracking',
}

whitelist_create = """
	create table if not exists %(table_whitelist)s (
		ip varchar(40) not null,
		unique (ip) 
	);
""".strip() % tables

tracking_create = """
	create table if not exists %(table_tracking)s (
		ip varchar(40) not null,
		first_seen timestamp not null,
		last_seen timestamp not null,
		last_blocked timestamp not null,
		good int not null default 0,
		bad int not null default 0,
		unique (ip) 
	);
""".strip() % tables


class Greylisting(response.ResponseTempFail):
	web_code = '4.1.1'
	message = 'Greylisting'


class GreyDatabase(PluginDatabase):
	debug = False
	database_schema = [whitelist_create, tracking_create]
	#cleanup_interval = 300

	def ignore (self, ip):
		query = "select 'true' as allow from %(table_whitelist)s where ip = ?" % tables
		res = self.fetchone(query,ip)
		return True if res else False

	def get (self, ip):
		query = "select ip, first_seen, last_seen, last_blocked, good, bad from %(table_tracking)s where ip = ?" % tables
		return self.fetchone(query,ip)
		
	def track (self, ip, timestamp, allowed):
		# try the fastpath, if it fails (and we have a raise) we give the sender one more free mail
		if allowed:
			query = "update %(table_tracking)s set last_seen = ?, good = good + 1 where ip = ?" % tables
			if self.update(query,timestamp,ip):
				return True
		else:
			query = "update %(table_tracking)s set last_seen = ?, last_blocked = ?, bad = bad + 1 where ip = ?" % tables
			if self.update(query,timestamp,timestamp,ip):
				return True

		# otherwise the slow path ..
		query = "insert into %(table_tracking)s (ip, first_seen, last_seen, last_blocked, good, bad) values (?, ?, ?, ?, ?, ?)" % tables
		if allowed:
			return self.insert(query,ip,timestamp,timestamp,'null',1,0)
		else:
			return self.insert(query,ip,timestamp,timestamp,timestamp,0,1)

	def cleanup (self, total_amnesia, inactivity_amnesia, threshold_amnesia, threshold):
		query = """delete from %(table_tracking)s where
				(first_seen is null or first_seen < ?) 
			or	(last_seen is null or last_seen < ?)
			or	(last_seen < ? and bad = 0 and good <= ?)
		""" % tables
		now = time.time()
		tl = now - total_amnesia
		iy = now - inactivity_amnesia
		td = now - threshold_amnesia
		if self.delete(query,tl,iy,td,threshold):
			return True
		return False
		
	def empty (self):
		#self.delete('delete from %(table_tracking)s' % tables)
		return True

class Grey(PostfixPlugin):
	debug = False
	factory = GreyDatabase

	def onInitialisation(self):
		self.training = self.configuration.get('training', False)

		self.use_whitelist = self.configuration.get('use_whitelist', True)
		self.threshold = self.configuration.get('threshold', 1)
		self.waiting_time = self.configuration.get('waiting_time', 60)

		self.total_amnesia = self.configuration.get('total_amnesia', 31*24*60*60)
		self.inactivity_amnesia = self.configuration.get('inactivity_amnesia', 4*24*60*60)
		self.threshold_amnesia = self.configuration.get('threshold_amnesia', 6*60*60)

		try:
			assert isinstance(self.training,           bool)
			assert isinstance(self.use_whitelist,      bool)
			assert isinstance(self.waiting_time,       int)
			assert isinstance(self.total_amnesia,      int)
			assert isinstance(self.inactivity_amnesia, int)
		except AssertionError:
			return False

                self.database.empty()
		return True

	def validateAttributes(self, message):
		try:
			assert message.get('client_address', None) is not None
			assert message.get('timestamp', None) is not None
			return True
		except AssertionError:
			return False

	def ignore(self, message):
		if not self.use_whitelist:
			return False
		return self.database.ignore(message['client_address'])

	def allowed(self, message):
		if self.waiting_time <= 0:
			return True

		info = self.database.get(message['client_address'])
		
		if info is None:
			return True if self.threshold else False
		try:
			count = int(info['good'])
		except (TypeError, ValueError):
			log.msg("failure accessing the grey database whilst reading 'good'")
			# This should never happen ever, fail open
			return True
		
		if self.threshold and count < self.threshold:
			return True

		try:
			last_blocked = float(info['last_blocked'])
		except (TypeError, ValueError):
			# last_blocked is null, never had a wrong message
			try:
				last_blocked = float(info['last_seen'])
			except:
				# This should never happend ever, fail open
				log.msg("failure accessing the grey database whilst reading 'last_seen'")
				return True

		return  message['timestamp']-last_blocked >= self.waiting_time

	def track (self,message,allowed):
		return self.database.track(message['client_address'],message['timestamp'],allowed)

	def check(self, message):
		if self.ignore(message):
			return response.ResponseContinue

		allowed = self.allowed(message)
		tracked = self.track(message,allowed)
		# fail open if we can not update DB
		if tracked and not allowed:
			return Greylisting

		return response.ResponseContinue
		
	def cleanup(self):
		self.database.cleanup(self.total_amnesia, self.inactivity_amnesia, self.threshold_amnesia, self.threshold)
		return True


plugin = Grey('grey', '2.1')
