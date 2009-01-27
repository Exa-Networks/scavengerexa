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
	valid = ['debug','port','timeout','smarthost','sender','recipient']

	def option_timeout (self):
		self.number('timeout',low=1)

        def option_smarthost (self):
		if self.has('smarthost'):
			self.set('smarthost')
		else:
			self._set('smarhost','127.0.0.1')

	def option_port (self):
		BaseOption.port(self,'port')

	def option_sender (self):
		if self.has('sender'):
			self.set('sender')
		else:
			self._set('sender','<scavenger-action@%s> ScavengerEXA' % socket.gethostname())
	
	def option_recipient (self):
		if self.has('recipient'):
			self.set('recipient')
		else:
			raise OptionError('option recipient, the mail recipient is a mandatory field')

