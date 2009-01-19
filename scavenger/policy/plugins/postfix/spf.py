#!/usr/bin/env python
# encoding: utf-8
"""
spf.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

import time
try:
	# SPF try to import DNSPython which may not be installed
	from scavenger.policy.tools import spf
except ImportError:
	pass

from twisted.python import log

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response

class SPFViolation(response.ResponseFail):
	web_code = '3.1.1'
	message = 'Mail blocked by SPF rule'

class SPF(PostfixPlugin):
	debug = False
	valid = ['pass', 'unknown', 'fail', 'error', 'softfail', 'none', 'neutral']

	def onInitialisation(self):
		try:
			# SPF try to import DNSPython which may not be installed
			from scavenger.policy.tools import spf
			return True
		except ImportError:
			self.errors = ['can not import SPF library or any of its dependencies']
			return False

	def requiredAttributes (self):
		return ['client_address','client_name'] # sender is not required as it can be null

	def check(self, message):
		ip = message.get('client_address')
		client_name = message.get('client_name')
		sender = message.get('sender', '')

		if not sender:
			return response.ResponseContinue

		try:
			result,_,_= spf.check(i=ip, s=sender, h=client_name)
			if self.debug: log.msg ("spf %s" % str(result))
		except spf.PermError:
			return response.DataError('can not perform SPF check with data ip=%s sender=%s host=%s' % (ip,sender,client_name))
		except spf.TempError:
			return response.DataError('can not perform SPF check with data ip=%s sender=%s host=%s' % (ip,sender,client_name))
		except spf.AmbiguityWarning:
			return response.Continue()
		except IndexError: # the spf library is buggy
			return response.ResponseContinue


		if result not in self.valid:
			return response.InternalError('The SPF library returned something unexpected %s' % str(result))

#		if result in ['fail', 'softfail']:
		if result in ['fail', ]:
			return SPFViolation()

		return response.ResponseContinue

plugin = SPF('spf', '2.1')
