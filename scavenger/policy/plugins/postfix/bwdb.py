#!/usr/bin/env python
# encoding: utf-8
"""
bwdb.py

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
	'table_bwlist_ip':        'bwl_ip',
	'table_bwlist_domain':    'bwl_domain',
}

bwlist_ip_create = """
	create table if not exists %(table_bwlist_ip)s (
		recipient_domain varchar(120) not null,
		ip varchar(40) not null,
		white boolean not null
	);
""".strip() % tables

bwlist_domain_create = """
	create table if not exists %(table_bwlist_domain)s (
		recipient_domain varchar(120) not null,
		sender_domain varchar(120) not null,
		white boolean not null
	);
""".strip() % tables



class WhitelistingIP(response.ResponseAccept):
	web_code = '1.1.1'
	message = 'Whitelisting'

class WhitelistingDomain(response.ResponseAccept):
	web_code = '1.1.2'
	message = 'Whitelisting'

class BlacklistingIP(response.ResponseFail):
	web_code = '1.1.3'
	message = 'Blacklisting'

class BlacklistingDomain(response.ResponseFail):
	web_code = '1.1.4'
	message = 'Blacklisting'



class Database (PluginDatabase):
	debug = False
	database_schema = [bwlist_ip_create, bwlist_domain_create]

	def getIPBWStatus(self, domain=None, ip=None, bw=None):
		query = "select white from %s" % tables['table_bwlist_ip']
		args = []

		if domain is not None:
			args.append(('recipient_domain', domain))
		if ip is not None:
			args.append(('ip', ip))
		if bw is not None:
			args.append(('white', bw))

		query = ' where '.join((query, ' and '.join(('%s = ?' % col for col, value in args))))
		args = [arg for name, arg in args]

		res = self.fetchall(query, *args)
		if not res:
			return None

		return res[0]['white'] in ('true', 't', True)

	def getDomainBWStatus(self, domain=None, sender_domain=None, bw=None):
		query = "select white from %s" % tables['table_bwlist_domain']
		args = []

		if domain is not None:
			args.append(('recipient_domain', domain))
		if sender_domain is not None:
			args.append(('sender_domain', sender_domain))
		if bw is not None:
			args.append(('white', bw))

		query = ' where '.join((query, ' and '.join(('%s = ?' % col for col, value in args))))
		args = [arg for name, arg in args]

		res = self.fetchall(query, *args)
		if not res:
			return None

		return res[0]['white'] in ('true', 't', True)


class BWDB(PostfixPlugin):
	debug = False
	factory = Database

	def onInitialisation(self):
		self.training = self.configuration.get('training', False)

		self.use_whitelist = bool(self.configuration.get('use_ip_whitelist', False))
		self.use_blacklist = bool(self.configuration.get('use_ip_blacklist', False))

		self.use_whitelist = bool(self.configuration.get('use_domain_whitelist', False))
		self.use_blacklist = bool(self.configuration.get('use_domain_blacklist', False))
		
		return True

	def isTraining(self):
		return self.training is True

	def getBWListedIP(self, domain, ip):
		if self.use_whitelist or self.use_blacklist:
			if self.use_whitelist and self.use_blacklist:
				type = None
			else:
				type = True if self.use_whitelist else False

			return self.database.getIPBWStatus(domain, ip, type)

	def getBWListedDomain(self, domain, sender_domain):
		if self.use_whitelist or self.use_blacklist:
			if self.use_whitelist and self.use_blacklist:
				type = None
			else:
				type = True if self.use_whitelist else False

			return self.database.getDomainBWStatus(domain, sender_domain, type)

	def check(self, message):
		if self.isTraining():
			return response.ResponseContinue

		recipient = message.get('recipient', None)
		if not recipient:
			return response.ResponseContinue

		try:
			user, domain = recipient.split('@')
		except ValueError:
			return response.DataError('invalid email address: %s' % recipient)

		ip = message.get('client_address', None)
		if ip is None:
			return response.DataError('no client ip address')

		try:
			res = self.getBWListedIP(domain, ip)
			if res is True:
				return WhitelistingIP
			if res is False:
				return BlacklistingIP

			sender = message.get('sender', None)
			# no sender if the mail is a bounce
			if not sender:
				return response.ResponseContinue

			try:
				sender_user, sender_domain = sender.split('@')
			except ValueError:
				return response.DataError('invalid sender email address: %s' % sender)

			res = self.getBWListedDomain(domain, sender_domain)
			if res is True:
				return WhitelistingDomain
			if res is False:
				return BlacklistingDomain

		except:
			return response.InternalError

		return response.ResponseContinue

plugin = BWDB('bwdb', '2.1')
