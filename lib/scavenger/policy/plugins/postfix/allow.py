#!/usr/bin/env python
# encoding: utf-8
"""
allow.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import re

from twisted.python import log

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response


class AllowUser(response.ResponseAccept):
	web_code = '0.0.0'


class Allow (PostfixPlugin):
	def onInitialisation(self):
		passthrough = self.configuration.get('users', '')
		self.passthrough = ['^'+p+('$' if p.count('@') else '@.*$') for p in passthrough.split()]
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

		for test in self.passthrough:
			if re.compile(test).match(recipient):
				return AllowUser('mail sent to an unblockable address <%s>' % recipient)

		return response.ResponseContinue


plugin = Allow('allow', '2.1')
