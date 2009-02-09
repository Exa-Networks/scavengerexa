#!/usr/bin/env python
# encoding: utf-8
"""
unfiltered.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement
import time

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import PluginDatabase
from scavenger.policy.plugin import response

tables = {
	'table_unfiltered_domains':        'unfiltered_domains',
}

unfiltered_domains_create = """
	create table if not exists %(table_unfiltered_domains)s (
		recipient_domain varchar(120) not null
	);
""".strip() % tables


class UnfilteredDomain(response.ResponseAccept):
	web_code = '0.0.0'
	message = 'in exa global whitelist'


class UnfilteredDB (PluginDatabase):
	debug = False # do we need to explicitly set this here?
	database_schema = [unfiltered_domains_create]

	def getUnfilteredStatus(self, domain):
		query = "select 'true' result from %s where recipient_domain = ?" % tables['table_unfiltered_domains']
		res = self.fetchall(query, domain)
		if not res:
			return False
		return res[0]['result'] in ('true', 't', True)


class Unfiltered(PostfixPlugin):
	debug = False
	factory = UnfilteredDB

	def getDatabase(self):
		return ['postgresql','sqlite3','mysql']

	def requiredAttributes(self):
		return ['recipient']

	def isUnfiltered(self, domain):
		return self.database.getUnfilteredStatus(domain)

	def check(self, message):
		recipient = message['recipient']
		
		try:
			user, domain = recipient.split('@')
		except ValueError:
			return response.DataError('invalid email address: %s' % recipient)

		try:
			res = self.isUnfiltered(domain)
			if res is True:
				return UnfilteredDomain

		except:
			return response.PluginError

		return response.ResponseContinue

unfiltered = Unfiltered('unfiltered', '2.1')
