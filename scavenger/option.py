#!/usr/bin/env python
# encoding: utf-8
"""
option.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import os
import socket

class OptionError (Exception): pass


class Option (dict):
	valid = ['debug','display']

	def __getattribute__ (self, key):
		try:
			return dict.__getattribute__(self,key)
		except AttributeError:
			pass
		try:
			return dict.__getitem__(self, key)
		except KeyError,e:
			raise AttributeError(str(e))

	def _env (self,value):
		return os.environ.get(value.lower(),os.environ.get(value.upper(),''))

	def _has (self,value):
		return os.environ.has_key(value.lower()) or os.environ.has_key(value.upper())

	def __init__ (self,*options):
		dict.__init__(self)

		if not len(options):
			options = self.valid

		for option in options:
			if not option in self.valid:
				raise OptionError('unknown configuration name %s' % option)

		for option in options:
			func = getattr(self,'_%s' % option)
			func()

	def _debug (self):
		# debug level
		if self._has('debug'):
			debug = self._env('debug')
			if debug.isdigit():
				self['debug'] = int(debug)
			else:
				self['debug'] = 1
		else:
			self['debug'] = 0

	def display (self):
		print "*"*80
		for option in self.valid:
			if self.has_key(option):
				print "%-20s : %s" %(option, self[option])
		print "*"*80

	def _slow (self):
		self['slow'] = self._has('slow')
 		self['slow'] = self._has('slow')
		if self['slow']:
			self['slow'] = not not self['slow']
			 
	def _balance (self):
		self['balance'] = self._has('balance')
		if self['balance']:
			self['balance'] = not not self['balance']


	def _validate_service (self,service):
		if not service.count(':'):
			raise OptionError('a service should be defined as host:port')
		host,port = service.split(':')
		try:
			ip = socket.gethostbyname(host)
		except socket.gaierror:
			raise OptionError ('could not resolve hostname %s' % host)
		try:
			port = int(port)
		except ValueError:
			raise OptionError('the port must be an integer, not a service name')
		return (ip,port)

	def _validate_cidr (self,cidr):
		if not cidr.count('/'):
			cidr+='/32'
		ip,mask = cidr.split('/')
		if ip.count(':'):
			raise OptionError('only IPv4 is currently supported')
		if ip.count('.') != 3:
			raise OptionError('invalid IP address within CIDR %s' % cidr)
		try:
			start = 0
			for c in [int(c) for c in ip.split('.')]:
				start <<= 8
				start += c
		except ValueError:
			raise OptionError('invalid IP address within CIDR %s' % cidr)
		try:
			mask = int(mask)
		except ValueError:
			raise OptionError('the netmask must be an integer not %s' % mask)

		if mask < 0 or mask > 32:
			raise OptionError('the netmask is invalid %d' % mask)

		s = pow(2,32-mask)

		if int(start/s) * s != start:
			raise OptionError('invalid netmask boundary')

		return cidr

if __name__ == '__main__':
	 option = Option().display()
