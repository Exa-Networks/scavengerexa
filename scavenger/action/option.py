#!/usr/bin/env python
# encoding: utf-8
"""
option.py

Created by Thomas Mangin on 2009-01-16.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import socket
from scavenger.option import Option as BaseOption, OptionError

class Option (BaseOption):
	valid = ['debug','slow','port','timeout','smarthost','sender','recipient']

	def __init__(self,*options):
		BaseOption.__init__(self,*options)

	def _timeout (self):
		limit = self._env('timeout')
		if not limit:
			self['timeout'] = 20
		elif limit.isdigit():
			self['timeout'] = int(limit)
		else:
			raise OptionError('timeout is not an integer')
		if self['timeout'] <= 0:
			raise OptionError('timeout is not a positive integer')

        def _smarthost (self):
		self['smarthost'] = self._env('smarthost')
		if not self['smarthost']:
			self['smarthost'] = '127.0.0.1'

	def _port (self):
		port = self._env('port')
		if not port:
			self['port'] = 25
		elif port.isdigit():
			self['port'] = int(port)
		else:
			raise OptionError('the port must be an integer')

	def _sender (self):
		self['sender'] = self._env('sender')
		if not self['sender']:
			self['sender'] = '<scavenger-action@%s> ScavengerEXA' % socket.gethostname()
	
	def _recipient (self):
		self['recipient'] = self._env('recipient')
		if not self['recipient']:
			raise OptionError('recipient email address needed')

