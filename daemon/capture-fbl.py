#!/usr/bin/env python
# encoding: utf-8
"""
capture.py

Created by Thomas Mangin on 2008-02-16.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import os
import sys
import time
import random
import socket

# Enabling (or not) psycho

try:
	import psyco
	psyco.full()
	print 'Psyco found and enabled'
except ImportError:
	print 'Psyco is not available'

# Options

from scavenger.tools.ip import *
from scavenger.option import Option as BaseOption, OptionError
from scavenger.cache import ExpirationCache as Cache
from scavenger.capture.fbl.parser import Parser

class Option (BaseOption):
	valid = ['debug','diffusion','internal','dispatch','interval','account']

	def option_diffusion (self):
		self.enum('diffusion',['none','rr','sh','all'])

	def option_internal (self):
		internal = []
		for cidr in self._list('internal'):
			internal.append(self._cidr('internal',cidr))
		if len(internal) < 1:
			raise OptionError('option internal please setup at least one ip range to monitor')
		self._set('internal',internal)

	def option_dispatch (self):
		dispatchs = []
		for dispatch in self._list('dispatch'):
			dispatchs.append(self._service('dispatch',dispatch))
		if len(dispatchs) < 1:
			raise OptionError('option dispatch please setup at least one dispatch')
		self._set('dispatch',dispatchs)

	def option_interval (self):
		self.number('interval',1,3600)
	
	def option_account (self):
		if not self.has('account'):
			raise OptionError('option capture fbl, please setup an email account to collect')
		account = self.get('account')
		try:
			proto,user,leftover = account.split(':')
			self._set('proto',proto)
			self._set('user',user)
			password,server = leftover.split('@')
			# XXX: This prints the password !!! 
			self._set('password',password)
			self._set('server',server)
		except (ValueError,IndexError):
			raise OptionError('option capture fbl, please setup an valid email account to collect proto:user:password')

try:
	option = Option(folder=os.path.join('scavenger','capture-fbl')).option
except OptionError, e:
	print str(e)
	sys.exit(1)

# Debugging

debug_option = not not option.debug & 1

if debug_option:
	option.display()
	print "+"*80

parser = Parser(option.server,option.user,option.password)

while True:
	for message in parser.parse():
		print message
	time.sleep(option.interval)
