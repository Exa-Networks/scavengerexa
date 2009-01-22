#!/usr/bin/env python
# encoding: utf-8
"""
helo.py

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
	'table_helo':	'helo',
}

create_helo = """
create table if not exists %(table_helo)s (
	client_address      varchar(40),

	helo                varchar(40),
	count               bigint default 0,

	first_seen          bigint default 0,
	last_seen           bigint default 0,

	primary key (client_address)
)
""".strip() % tables

# -------------------------------------------------------------------


class InconstantHelo (response.ResponseFilter):
	duration = 24*60*60

class TooManyHelo (response.ResponseFilter):
	message = 'The source IP has too many different HELO'
	duration = 24*60*60

class HeloDB (PluginDatabase):
	debug = False
	database_schema = [create_helo,]

	def new (self,client,helo):
		replacement = tables.copy()
		replacement['now'] = "%d" % int(time())
		replacement['string'] = '%s'
		query = "INSERT INTO %(table_helo)s (client_address,helo,first_seen) VALUES (%(string)s,%(string)s,%(now)s)" % replacement
		self.insert(query,client,helo)

	def increment (self,client,helo):
		query = "UPDATE %(table_helo)s SET count=count+1 WHERE client_address = %%s AND helo = %%s" %  tables
		return self.insert(query,client,helo)

	def nb_hello (self,client):
		query ="""
SELECT
	count(*) as sum,
FROM
	%(table_helo)s
WHERE
	client_address = %%s
""" % tables
		return self.fetchone(query, client)

	def nb_connection (self,client):
		query ="""
SELECT
	sum(helo) as sum,
FROM
	%(table_helo)s
WHERE
	client_address = %%s
""" % tables
		return self.fetchone(query, client)

	def cleanup (self):
		before = int(time()) - 31*24*60*60
		query = "DELETE FROM %(table_helo)s where (first_seen != 0 and first_seen < %%s)" % tables
		query = query % before
		return self.delete(query)


class Helo (ScavengerPlugin):
	debug = True
	factory = HeloDB

	def onInitialisation (self):
		self.max_helo = self.configuration.get('max_helo', 0)
		return True

	def getProtocols (self):
		return ['scavenger_access_policy']

	def getDatabase (self):
		return ['postgresql','sqlite3','mysql']

	def requiredAttributes (self):
		return ['client_address','server_address','helo_name']

	def update (self, message):
		client = message['client_address']
		client = message['server_address']
		helo = message['helo_name']
		
		if not self.database.increment(client,server,helo):
			try:
				self.database.new(client,server)
			except self.database.api2.IntegrityError:
				pass
			finally:
				self.database.increment(client,server,helo)
		
	def check (self,message):
		client = message['client_address']

		if self.max_helo:
			r = self.database.nb_helo(client)
			if r is None:
				# This should be impossible ..
				return response.ResponseContinue()
		
			if r['sum']  > self.max_strict_hello:
				return TooManyHelo()
		
		return response.ResponseContinue()

	def cleanup(self):
		self.database.cleanup()

plugin = Helo('helo', '1.0')
