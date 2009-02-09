#!/usr/bin/env python
# encoding: utf-8
"""
deny.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import re

from twisted.python import log

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response


class DenyUser(response.ResponseFail):
	web_code = '5.9.0'


class Deny (PostfixPlugin):
	def onInitialisation(self):
		blocked = self.configuration.get('users', '')
		self.blocked = ['^'+p+('$' if p.count('@') else '@.*$') for p in blocked.split()]
		return True

	def requiredAttributes(self):
		return ['recipient'] # sender could be a bounce
	
	def check(self, message):
		recipient = message['recipient']
		try:
			user, domain = recipient.split('@')
		except ValueError:
			log.logerr.write('the recipient did not contain exactly one @')
			return response.ResponseContinue

		for test in self.blocked:
			if re.compile(test).match(recipient):
				return DenyUser('mail sent to a blocked address <%s>' % recipient)

		sender = message.get('sender','')
		if not sender:
			# got a bounce
			return response.ResponseContinue
		
		try:
			user, domain = sender.split('@')
		except ValueError:
			log.logerr.write('the sender did not contain exactly one @')
			return response.ResponseContinue

		for test in self.blocked:
			if re.compile(test).match(sender):
				return DenyUser('mail sent from an blocked address <%s>' % sender)

		return response.ResponseContinue


plugin = Deny('deny', '2.1')
