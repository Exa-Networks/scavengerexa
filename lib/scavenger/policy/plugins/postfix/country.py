#!/usr/bin/env python
# encoding: utf-8
"""
country.py

Created by David Farrar on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement
import time

from scavenger.policy.plugin import PostfixPlugin
from scavenger.policy.plugin import response

try:
	import GeoIP
except ImportError:
	pass

class JingoMail(response.ResponseFail):
	web_code = '2.3.1'
	message = 'Sender outside UK/US has no DNS reverse'

		
class Country(PostfixPlugin):
	def onInitialisation(self):
		try:
			import GeoIP
			self.checker = GeoIP.open('/usr/share/GeoIP/GeoIP.dat', GeoIP.GEOIP_MEMORY_CACHE)
			# XXX: Should not really harcode our own IP
			if self.countryOK('82.219.5.1'):
				return True
			self.errors = ['self test failed']
			return False
		except ImportError:
			self.errors = ['can not import GeoIP library']
			return False

	def isTraining(self):
		res = self.configuration.get('training', False)
		return res is True

	def countryOK(self, ip):
		country = self.checker.country_code_by_addr(ip)
		if country is None:
			return None
		return country.lower() in self.configuration.get('allowed_countries', '').split(' ')

	def check(self, message):
		if self.isTraining():
			return response.ResponseContinue

		ip = message.get('client_address', None)
		if ip is None:
			return response.DataError('no client ip address')
		try:
			res = self.countryOK(ip)
			if res is False:
				if message.get('client_name', None) is None:
					return JingoMail

		except:
			return response.InternalError

		return response.ResponseContinue

plugin = Country('country', '2.1')
