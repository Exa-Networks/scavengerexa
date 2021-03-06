#!/usr/bin/env python
# encoding: utf-8
"""
allow.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import re

from twisted.python import log

from scavenger.policy.plugin import ScavengerPlugin
from scavenger.policy.plugin import response


class AllowUser(response.ResponseAccept):
	duration = 24*60*60


class Allow (ScavengerPlugin):
	def onInitialisation(self):
		passthrough = self.configuration.get('users', '')
		self.passthrough = ['^'+p+('$' if p.count('@') else '@.*$') for p in passthrough.split()]
		return True
	
	def requiredAttributes (self):
		return ['recipient']

	def check(self, message):
		recipient = message['recipient']
		try:
			user, domain = recipient.split('@')
		except ValueError:
			log.logerr.write('the recipient did not contain exactly one @')
			return response.ResponseContinue

		for test in self.passthrough:
			if re.compile(test).match(recipient):
				return AllowUser('mail sent to an unblockable address <%s>' % recipient)

		return response.ResponseContinue


plugin = Allow('allow', '1.0')
