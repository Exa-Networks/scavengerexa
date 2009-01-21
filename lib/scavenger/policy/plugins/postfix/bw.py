#!/usr/bin/env python
# encoding: utf-8
"""
bw.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

try:
	from vdomain.client import Client as vmailClient, VmailError
except ImportError:
	pass

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response


class NoSuchUser(response.ResponseFail):
	web_code = '1.2.1'
	message = 'The recipient does not exist'


class WhitelistingDomain(response.ResponseAccept):
	web_code = '1.1.2'
	message = 'Whitelisting'

class BlacklistingIP(response.ResponseFail):
	web_code = '1.1.3'
	message = 'Blacklisting'

class BlacklistingDomain(response.ResponseFail):
	web_code = '1.1.4'
	message = 'Blacklisting'



class VmailBWList(PostfixPlugin):
	def onInitialisation(self):
		try:
			from vdomain.client import Client as vmailClient, VmailError
		except ImportError:
			return False
		self.host = self.configuration.get('host')
		self.port = self.configuration.get('port')
		self.password = self.configuration.get('vmail_password')
		return True

	def requiredAttributes (self):
		return ['sender','recipient']

	def vmail_checkbwlist (self,domain,user,sender):
		check = (
			(lambda: vmailClient(self.host, self.port, domain, self.password).getoption(user, 'whitelist'), True),
			(lambda: vmailClient(self.host, self.port, domain, self.password).getoption(user, 'blacklist'), False),
			(lambda: vmailClient(self.host, self.port, domain, self.password).getoption('', 'whitelist'), True),
			(lambda: vmailClient(self.host, self.port, domain, self.password).getoption('', 'blacklist'), False),
		)

		for function, bw in check:
			try:
				list = function()
			# XXX: fix this exception later
			except:
				return None

			if list is None:
				continue

			for entry in list:
				if not entry:
					continue

				if entry[1:].count('@'):
					if sender == entry:
						return bw
				else:
					if entry[0] not in ('.', '@'):
						entry = '@' + entry
					if sender.endswith(entry):
						return bw

		return None

	def check(self, message):
		recipient = message.get('recipient', '')
		sender = message.get('sender', '')

		# bounce mail can not be whitelisted
		if sender is '':
			return response.ResponseContinue

		try:
			user, domain = recipient.split('@')
		except ValueError:
			return response.DataError('invalid recipient email address: %s' % recipient)

		ldap_domains = [d for d in self.configuration.get('ldap_domains', '').split(' ') if d]

		if domain not in ldap_domains:
			_response = self.vmail_checkbwlist(domain, user, sender)
			if _response is True:
				return WhitelistingDomain
			if _response is False:
				return BlacklistingDomain

		return response.ResponseContinue


vmaillist = VmailBWList('bw', '2.1')
