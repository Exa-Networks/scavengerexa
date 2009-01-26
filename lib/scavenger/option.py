#!/usr/bin/env python
# encoding: utf-8
"""
option.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import sys
import optparse
import socket

class OptionError (Exception): pass


class Option (dict):
	valid = ['debug','display']

	def __init__ (self,folder='',options=()):
		dict.__init__(self)
		
		self.etc = os.environ.get('ETC','/etc')
		self.cache = os.environ.get('CACHE','/var/cache')
		
		self.__path = os.path.join(self.etc,folder)
		
		if folder:
			# the self.options keys
			if self.__keys == ():
				self.__keys = lambda: self.__files()
			else:
				self.__keys = lambda: [option for option in options]
		else:
			if len(options):
				self.__keys = lambda: set(options)
			else:
				self.__keys = lambda: self.valid
		self.options = {}
		
		self.__reload()
		
	def __files (self):
		# XXX: should really use glob.glob for that.
		for walk in os.walk(self.__path):
			for f in walk[2]:
				if f[0] != '.' and f[-1] != '~':
					yield f
			break
	
	def __reload(self):
		self.clear()
		
		options = self.__keys()

		for option in options:
			if not option.lower() in self.valid:
				raise OptionError('unknown configuration name %s' % option)

		parser = optparse.OptionParser()
		for option in options:
			parser.add_option('','--%s' % option,action="store",type="str")
		opts,_ = parser.parse_args()
		
		for option in options:
			if getattr(opts,option) != None:
				self.options[option.lower()] = getattr(opts,option)
				continue
			if os.environ.has_key(option):
				value = os.environ.get(option)
				value.strip()
				self.options[option.lower()] = value
				continue
			if  os.path.isfile(option):
				lines = []
				with open(option,'r') as reader:
					for line in reader.readlines():
						line = line.strip()
						if line == '' or line[0] == '#':
							continue
						lines.append(line)
					self.options[option.lower()] = ' '.join(lines)
					continue
			raise OptionError('no value for configuration name %s' % option)
		
		for option in options:
			func = getattr(self,'_%s' % option)
			func()
	
	def __getattribute__ (self, key):
		try:
			return dict.__getattribute__(self,key)
		except AttributeError:
			pass
		try:
			return dict.__getitem__(self, key)
		except KeyError,e:
			raise AttributeError(str(e))

	def _env (self,key):
		return self.options.get(key.lower(),'')

	def _has (self,key):
		return self.options.has_key(key.lower())

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
			 
	def _diffusion (self):
		self['diffusion'] = self._env('diffusion')
		if not self['diffusion']:
			raise OptionError('diffusion method is not set (one: do not balance traffic, rr: roundrobin between sources, sh: sourcehash sender, all: send a copy to every server)')
		if self['diffusion'] not in ['none','rr','sh','all']:
			raise OptionError('diffusion method is not set (one: no balancing, rr: roundrobin, sh: sourcehash, all: every destination)')


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
