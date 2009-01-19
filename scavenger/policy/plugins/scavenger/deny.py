#!/usr/bin/env python
# encoding: utf-8
"""
deny.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import re

from twisted.python import log

from scavenger.policy.plugin import ScavengerPlugin
from scavenger.policy.plugin import response


class DenyUser(response.ResponseBlock):
	duration = 24*60*60


class Deny (ScavengerPlugin):
	def getProtocols (self):
		return ['scavenger_access_policy']

	def onInitialisation(self):
		blocked = self.configuration.get('users', '')
		self.blocked = ['^'+p+('$' if p.count('@') else '@.*$') for p in blocked.split()]
		return True
	
	def validateAttributes(self, message):
		try:
			assert isinstance(message.get('recipient', None), str)
			return True
		except AssertionError:
			return False

	def check(self, message):
		recipient = message.get('recipient', None)
		try:
			user, domain = recipient.split('@')
		except ValueError:
			log.logerr.write('the recipient did not contain exactly one @')
			return response.ResponseContinue

		for test in self.blocked:
			if re.compile(test).match(recipient):
				return DenyUser('mail sent to a blocked address <%s>' % recipient)

		sender = message.get('sender',None)
		try:
			user, domain = sender.split('@')
		except ValueError:
			log.logerr.write('the sender did not contain exactly one @')
			return response.ResponseContinue

		for test in self.blocked:
			if re.compile(test).match(sender):
				return DenyUser('mail sent from an blocked address <%s>' % sender)

		return response.ResponseContinue


plugin = Deny('deny', '1.0')
