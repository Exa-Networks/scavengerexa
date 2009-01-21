#!/usr/bin/env python
# encoding: utf-8
"""
reverse.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

try:
	from scavenger.policy.tools import dnscache
	import GeoIP
except ImportError:
	pass

import time

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response

try:
	import GeoIP
except ImportError:
	pass

class Reverse(PostfixPlugin):
	def onInitialisation(self):
		try:
			self.delay = int(self.configuration.get('delay_time', 0))
		except (ValueError,TypeError):
			self.delay = 0

		try:
			# XXX: we should not call an internal version as it can fail as well, what the point
			from scavenger.policy.tools import dnscache
		except ImportError,e:
			self.errors = ['can not find one of the dns library needed']
			return False
		try:
			import GeoIP
			self.checker = GeoIP.open('/usr/share/GeoIP/GeoIP.dat', GeoIP.GEOIP_MEMORY_CACHE)
			# XXX: Should not really harcode our own IP
			if self.countryOK('82.219.0.0'):
				return True
			self.errors = ['self test failed']
			return False
		except ImportError:
			self.errors = ['can not import GeoIP library']
			return False

	def countryOK(self, ip):
		country = self.checker.country_code_by_addr(ip)
		if country is None:
			return None
		return country.lower() in self.configuration.get('allowed_countries', [])

	def check(self, message):
		ip = message.get('client_address', None)
		client_name = message.get('client_name', None)
		if ip is None:
			return response.DataError('no client ip address')

		try:
			try:
				res = self.countryOK(ip)
			except socket.error:
				return response.DataError('something was wrong with the provided ip address')

			if res is False:
				try:
					ips = dnscache.getIpForName(client_name)
				except dnscache.DNSCacheError:
					return response.ResponseContinue()
				except IndexError:
					return response.ResponseContinue()
					
				if ip not in ips:
					return response.ResponseContinue()

				# XXX: Where is the end of the code ???
				# XXX: Where are we blocking the message ??

		except Exception, e:
			print e.__class__, e.message
			return response.InternalError()
		except:
			return response.InternalError()

		return response.ResponseContinue()

plugin = Reverse('reverse', '2.1')
