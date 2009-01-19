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


class Database (PluginDatabase):
	def getUnfilteredStatus(self, domain):
		query = "select 'true' result from %s where recipient_domain = ?" % tables['table_unfiltered_domains']
		res = self.fetchall(query, domain)
		if not res:
			return False
		return res[0]['result'] in ('true', 't', True)


class Unfiltered(PostfixPlugin):
	schema = [unfiltered_domains_create]
	database_factory = Database

	def isUnfiltered(self, domain):
		return self.database.getUnfilteredStatus(domain)

	def check(self, message):
		recipient = message.get('recipient', None)

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
