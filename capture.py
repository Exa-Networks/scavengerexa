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

from scavenger.tools.ip import *
from scavenger.option import Option as BaseOption, OptionError
from scavenger.cache import ExpirationCache as Cache
from scavenger.capture.wire import Wire
from scavenger.capture.parser import Parser
from scavenger.dispatch.message import DispatchMessageFactory, FactoryError

class Option (BaseOption):
	valid = ['debug','slow','diffusion','promiscuous','interface','internal','dispatch']

	def _promiscuous (self):
		# should the interface be in promiscuous mode
		self['promiscuous'] = self._has('promiscuous')
	
	def _interface (self):
		if not self._has('interface'):
			self['interface'] = None
		else:
			self['interface'] = self._env('interface')

	def _internal (self):
		# get the networks to monitor
		self['internal'] = []

		for cidr in self._env('internal').split(' '):
			if not cidr:
				continue
			self['internal'].append(self._validate_cidr(cidr))

		if len(self['internal']) < 1:
			raise OptionError('please setup at least one CIDR to monitor, separated by space if multiple servers')


	def _dispatch (self):
		# get where to send the information gathered
		self['dispatch'] = []

		for dispatch in self._env('dispatch').split(' '):
			if not dispatch:
				continue
			self['dispatch'].append(self._validate_service(dispatch))

		if len(self['dispatch']) < 1:
			raise OptionError('please setup at least one dispatch, separated by space if multiple dispatchs')

#	def _memcache (self):
#		self['memcache'] = []
#
#		for server in self._env('memcache').split(' '):
#			if not server:
#				continue
#			self['memcache'].append(self._validate_service(server))
#
#		if len(self['memcache']) < 1:
#			raise OptionError('please setup at least one memcache server, separated by space if multiple servers')



try:
	option = Option()
except OptionError, e:
	print str(e)
	sys.exit(1)

debug_option = not not option.debug & 1
debug_parser = not not option.debug & 2
debug_cache = not not option.debug & 4
debug_udp = not not option.debug & 8
debug_wire = not not option.debug & 16

# Enabling (or not) psycho

if not option['slow']:
	try:
		import psyco
		psyco.full()
		print 'Psyco found and enabled'
	except ImportError:
		print 'Psyco is not available'

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
cmf = DispatchMessageFactory()

while True:
	for (si,sp),(di,dp),data in Wire(interface=option.interface,promiscuous=option.promiscuous):
		if debug_wire:
			print >> sys.stderr, "# %s:%d -> %s:%d" % (toips(si),sp,toips(di),dp)
			print >> sys.stderr, data
			print >> sys.stderr, '_'*80

		try:
			capture = parser.select(si,sp,di,dp).parse(data)
		except FactoryError,e:
			print >> sys.stderr, "%s:%d -> %s:%d : %s" % (toips(si),sp,toips(di),dp,str(e))

		if capture is None:
			continue
		message = cmf.fromCapture(capture)
		if debug_udp:
			print message
		send_udp(option.diffusion,message['si'],option.dispatch,message)


