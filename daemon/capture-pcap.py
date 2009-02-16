#!/usr/bin/env python
# encoding: utf-8
"""
capture.py

Created by Thomas Mangin on 2008-12-17.
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
from scavenger.capture.pcap.wire import Wire
from scavenger.capture.pcap.parser import Parser

class Option (BaseOption):
	valid = ['debug','diffusion','promiscuous','interface','internal','dispatch','ports']

	def option_diffusion (self):
		self.enum('diffusion',['none','rr','sh','all'])

	def option_promiscuous (self):
		self.boolean('promiscuous')
	
	def option_interface (self):
		if self.has('interface'):
			self.set('interface')
		else:
			self._set('interface',None)

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

	def option_ports (self):
		# the ports to monitor
		pass

try:
	option = Option(folder=os.path.join('scavenger','capture-pcap')).option
except OptionError, e:
	print str(e)
	sys.exit(1)

# Debugging

debug_option = not not option.debug & 1
debug_parser = not not option.debug & 2
debug_cache = not not option.debug & 4
debug_udp = not not option.debug & 8
debug_wire = not not option.debug & 16

if debug_option:
	option.display()
	print "debug parser", debug_parser
	print "debug cache ", debug_cache
	print "debug udp   ", debug_udp
	print "debug wire  ", debug_wire
	print "+"*80

# This time is the time we assume the spammer will not wait between headers after which we forget a conversation
cache = Cache(65,debug_cache)
parser = Parser(cache,option.internal,debug_parser)

while True:
	for (si,sp),(di,dp),data in Wire(interface=option.interface,promiscuous=option.promiscuous):
		if debug_wire:
			print >> sys.stderr, "# %s:%d -> %s:%d" % (toips(si),sp,toips(di),dp)
			print >> sys.stderr, data
			print >> sys.stderr, '_'*80

		try:
			message = parser.select(si,sp,di,dp).parse(data)
		except FactoryError,e:
			print >> sys.stderr, "%s:%d -> %s:%d : %s" % (toips(si),sp,toips(di),dp,str(e))

		if message is None:
			continue

		if debug_udp:
			print message

		send_udp(option.diffusion,message['si'],option.dispatch,message)


