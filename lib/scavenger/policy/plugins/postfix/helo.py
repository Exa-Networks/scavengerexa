#!/usr/bin/env python
# encoding: utf-8
"""
helo.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

try:
	import dns.resolver, dns.exception
except ImportError:
	pass

import re

from scavenger.tools import ip

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response

class HeloInvalid(response.ResponseFail):
	web_code = '1.1.1'
	message = 'helo/ehlo must be a FQDN or an address literal'

class HeloUnresolvable(response.ResponseFail):
	web_code = '1.2.1'
	message = 'helo/ehlo must have a valid A or MX record'

# XXX: TEST NOT CODED
class HeloNotSelf(response.ResponseFail):
	web_code = '1.2.2'
	message = 'helo/ehlo name must resolve to the IP of the mailserver'


class Helo(PostfixPlugin):
	def onInitialisation(self):
		self.valid_check_re = re.compile('^[\w-]+(\.[\w-]+)+$')
		self.reject_ip = self.configuration.get('reject_ip_address', False)
		self.check_fmt = self.configuration.get('check_format', False)
		self.check_resolv = self.configuration.get('check_resolvable', False)
		try:
			import dns.resolver, dns.exception
			return True
		except ImportError:
			self.errors = ['can not import dns library']
			return False

	def check_resolvable(self, helo):
		try:
			try:
				dns.resolver.query(helo, 'A')
				return True
			except dns.resolver.NoAnswer:
				pass
			try:
				dns.resolver.query(helo, 'MX')
				return True
			except dns.resolver.NoAnswer:
				pass

			return False
		except dns.resolver.NXDOMAIN:
			return False # the domain does not exist
		except dns.exception.DNSException:
			return True # something went wrong that we didn't expect
	
	def check_format(self, helo):
		return self.valid_check_re.match(helo) is not None
	
	def check(self, message):
		helo = message.get('helo_name','')
		if not helo:
			return HeloInvalid

		try:
			if self.reject_ip:
				if ip.isip(helo):
					return HeloInvalid

			if self.check_fmt:
				if not self.check_format(helo):
					return HeloInvalid

			if self.check_resolv:
				if not self.check_resolvable(helo):
					return HeloUnresolvable

		except:
			return response.InternalError('an unknown error occured')

		return response.ResponseContinue

helo = Helo('helo', '2.1')
