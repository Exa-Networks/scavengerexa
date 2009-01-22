#!/usr/bin/env python
# encoding: utf-8
"""
ratio.py

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
	'table_ratio':	'ratio',
}

create_ratio = """
create table if not exists %(table_ratio)s (
	client_address      varchar(40),
	server_address      varchar(40),

	h2                int default 0,
	h4                int default 0,
	h5                int default 0,

	m2                int default 0,
	m4                int default 0,
	m5                int default 0,

	r2                int default 0,
	r4                int default 0,
	r5                int default 0,

	d3                int default 0,
	d4                int default 0,
	d5                int default 0,

	e2                int default 0,
	e4                int default 0,
	e5                int default 0,

	first_seen          bigint default 0,
	last_seen           bigint default 0,

	primary key (client_address,server_address)
)
""".strip() % tables

# -------------------------------------------------------------------


class TooManyRejections (response.ResponseFilter):
	duration = 24*60*60


class RatioDB (PluginDatabase):
	debug = False
	database_schema = [create_ratio,]

	def new (self,client,server):
		replacement = tables.copy()
		replacement['now'] = "%d" % int(time())
		replacement['string'] = '%s'
		query = "INSERT INTO %(table_ratio)s (client_address,server_address,first_seen) VALUES (%(string)s,%(string)s,%(now)s)" % replacement
		self.insert(query,client,server)

	def increment (self,client,server,state,code):
		replacement = tables.copy()
		replacement['code'] = "%s%s" % (state[0],code[0])
		query = "UPDATE %(table_ratio)s SET %(code)s=%(code)s+1 WHERE client_address = %%s AND server_address = %%s" % replacement
		return self.insert(query,client,server)

	def stats (self,client):
		query ="""
SELECT
	sum(h2) as h2,
	sum(h4) as h4,
	sum(h5) as h5,
	
	sum(m2) as m2,
	sum(m4) as m4,
	sum(m5) as m5,
	
	sum(r2) as r2,
	sum(r4) as r4,
	sum(r5) as r5,
	
	sum(d3) as d3,
	sum(d4) as d4,
	sum(d5) as d5,
	
	sum(e2) as e2,
	sum(e4) as e4,
	sum(e5) as e5
FROM
	%(table_ratio)s
WHERE
	client_address = %%s
""" % tables
		return self.fetchone(query, client)

	def cleanup (self):
		before = int(time()) - 24*60*60
		query = "DELETE FROM %(table_ratio)s where (first_seen != 0 and first_seen < %%s)" % tables
		query = query % before
		return self.delete(query)


class Ratio (ScavengerPlugin):
	debug = True
	factory = RatioDB

	def onInitialisation (self):
		self.codes = {
			'ehlo' :        ['2','4','5'],
			'helo' :        ['2','4','5'],
			'mail' :        ['2','4','5'],
			'rcpt' :        ['2','4','5'],
			'data' :        ['3','4','5'],
			'end-of-data' : ['2','4','5'],
		}
		return True

	def getProtocols (self):
		return ['scavenger_access_policy']

	def getDatabase (self):
		return ['postgresql','sqlite3','mysql']

	def requiredAttributes (self):
		return ['client_address','server_address','protocol_state','code']

	def update (self, message):
		client = message['client_address']
		#server = message['server_address']
		server = '0.0.0.0'
		state = message['protocol_state'].lower()
		code = message['code']
	
		if code[0] in self.codes.get(state,[]):
			# XXX: well, is this not some horrible code prone to race !!
			if not self.database.increment(client,server,state,code):
				try:
					self.database.new(client,server)
				except self.database.api2.IntegrityError:
					pass
				finally:
					self.database.increment(client,server,state,code)

	def check (self, message):
		client = message['client_address']
	
		r = self.database.stats(client)
		if r is None:
			# This should be impossible ..
			return response.ResponseContinue()

		# XXX: not enough data so say anything

		if r['h2']+r['h4']+r['h5'] < 50:
			return response.ResponseContinue
	
		# simple tests to get something
		if r['h4']+r['h5'] > r['h2']:
			return TooManyRejections('too many "helo/ehlo" errors, relative to the number of mails')
		if r['m4']+r['m5'] > r['m2']:
			return TooManyRejections('too many "mail from" errors, relative to the number of mails')
		if r['d4']+r['d5'] > r['d3']:
			return TooManyRejections('too many "data" errors, relative to the number of mails')
		if r['e4']+r['e5'] > r['e2']:
			return TooManyRejections('too many "end-of-data" errors, relative to the number of mails')
		if r['d3']*3 < r['h2']:
			return TooManyRejections('not enough valid "data" relative to the number of "helo"')

		return response.ResponseContinue()


	def cleanup(self):
		self.database.cleanup()

plugin = Ratio('ratio', '1.0')
