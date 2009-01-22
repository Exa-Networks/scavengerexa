#!/usr/bin/env python
# encoding: utf-8
"""
spread.py

Created by Thomas Mangin on 2009-01-01.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

from time import time
from twisted.python import log

from scavenger.policy.plugin import ScavengerPlugin
from scavenger.policy.plugin import PluginDatabase
from scavenger.policy.plugin import response

tables = {
	'table_spread':	'spread',
}

create_spread = """
create table if not exists %(table_spread)s (
	client_address      varchar(40),
	server_address      varchar(40),

	count               bigint default 0,

	first_seen          bigint default 0,
	last_seen           bigint default 0,

	primary key (client_address,server_address)
)
""".strip() % tables

# -------------------------------------------------------------------


class InconstantSpread (response.ResponseFilter):
	duspreadn = 24*60*60

class TooManySpread (response.ResponseFilter):
	message = 'The source IP has too many different HELO'
	duspreadn = 24*60*60

class SpreadDB (PluginDatabase):
	debug = False
	database_schema = [create_spread,]

	def new (self,client,server):
		replacement = tables.copy()
		replacement['now'] = "%d" % int(time())
		replacement['string'] = '%s'
		query = "INSERT INTO %(table_spread)s (client_address,server_address,first_seen) VALUES (%(string)s,%(string)s,%(now)s)" % replacement
		self.insert(query,client,server)

	def increment (self,client,server):
		query = "UPDATE %(table_spread)s SET count=count+1 WHERE client_address = %%s AND server_address = %%s" %  tables
		return self.insert(query,client,server)

	def nb_server (self,client):
		query ="""
SELECT
	count(*) as sum,
FROM
	%(table_spread)s
WHERE
	client_address = %%s
""" % tables
		return self.fetchone(query, client)

	def cleanup (self):
		before = int(time()) - 31*24*60*60
		query = "DELETE FROM %(table_spread)s where (first_seen != 0 and first_seen < %%s)" % tables
		query = query % before
		return self.delete(query)


class Spread (ScavengerPlugin):
	debug = True
	factory = SpreadDB

	def onInitialisation (self):
		self.max_spread = self.configuration.get('max_spread', 0)
		return True

	def getProtocols (self):
		return ['scavenger_access_policy']

	def getDatabase (self):
		return ['postgresql','sqlite3','mysql']

	def requiredAttributes (self):
		return ['client_address','server_address','spread']

	def update (self, message):
		client = message['client_address']
		client = message['server_address']
		spread = message['spread']
		
		if not self.database.increment(client,server,spread):
			try:
				self.database.new(client,server)
			except self.database.api2.IntegrityError:
				pass
			finally:
				self.database.increment(client,server)
		
	def check (self, message):
		client = message['client_address']

		if self.max_spread:
			r = self.database.nb_spread(client)
			if r is None:
				# This should be impossible ..
				return response.ResponseContinue()
		
			if r['sum']  > self.max_strict_hello:
				return TooManySpread()
		
		return response.ResponseContinue()


	def cleanup(self):
		self.database.cleanup()

plugin = Spread('spread', '1.0')
