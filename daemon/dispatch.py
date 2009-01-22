#!/usr/bin/env python
# encoding: utf-8
"""
dispatch.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import sys

from scavenger.option import Option as BaseOption, OptionError
from scavenger.tools.ip import tostartend

class Option (BaseOption):
	valid = ['debug','slow','policy','filter','action','time']

	def _policy (self):
		# get where to send the information gathered
		self['policy'] = []
		for policy in self._env('policy').split(' '):
			if not policy:
				continue
			self['policy'].append(self._validate_service(policy))
		if len(self['policy']) < 1:
			raise OptionError('please setup at least one policy server, separated by spaces if multiple policy servers')

	def _filter (self):
		self['filter'] = self._env('filter').split(' ')

	def _action (self):
		self['action'] = {}
		for action in self._env('action').split(' '):
			if not action:
				continue
			parts = action.split('>')
			if len(parts) != 2:
				raise OptionError('an action is of the syntax networks/netmask>server:port')
			cidr = self._validate_cidr(parts[0].strip())
			service = self._validate_service(parts[1].strip())
			se = tostartend(cidr)
			if se not in self['action']:
				self['action'][se] = []
			self['action'][se].append(service)
		if len(self['action'].keys()) < 1:
			raise OptionError('please setup at least one action server, separated by spaces if multiple action servers')

	def _time (self):
		try:
			self['time'] = int (self._env('time'))
		except ValueError:
			raise OptionError('please setup how long should new spam from a IP should be ignore after first detection')

try:
	option = Option()
except OptionError,e:
	print str(e)
	sys.exit(1)

# Enabling (or not) psycho

if not option['slow']:
	try:
		import psyco
		psyco.full()
		print 'Psyco found and enabled'
	except ImportError:
		print 'Psyco is not available'

debug_option = not not option.debug & 1

if debug_option:
	option.display()
	print "+"*80

from scavenger.dispatch.server import DispatchFactory

factory = DispatchFactory(option.policy,option.filter,option.action,option.time)

from twisted.internet import reactor

reactor.listenUDP(25252, factory.buildProtocol())
reactor.run()
