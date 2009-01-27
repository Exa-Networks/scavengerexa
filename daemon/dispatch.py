#!/usr/bin/env python
# encoding: utf-8
"""
dispatch.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import os
import sys

# Enabling (or not) psycho

try:
	import psyco
	psyco.full()
	print 'Psyco found and enabled'
except ImportError:
	print 'Psyco is not available'

# Options

from scavenger.option import Option as BaseOption, OptionError
from scavenger.tools.ip import tostartend

class Option (BaseOption):
	valid = ['debug','policy','filter','action','time','validate']

	def option_policy (self):
		# get where to send the information gathered
		policies = []
		for policy in self._list('policy'):
			policies.append(self._service('policy',policy))
		if len(policies) < 1:
			raise OptionError('option policy, please setup at least one policy server')
		self._set('policy',policies)

	def option_filter (self):
		self.list('filter')

	def option_action (self):
		actions = {}
		for action in self._list('action'):
			source,destination = action.split('>',1)
			cidr = self._cidr('action source',source.strip())
			service = self._service('action destination',destination.strip())
			se = tostartend(cidr)
			if se not in actions:
				actions[se] = []
			actions[se].append(service)
		if len(actions.keys()) < 1:
			raise OptionError('option action, please setup at least one action server')
		self._set('action',actions)

	def option_time (self):
		self.number('time',low=0)

	def option_validate (self):
		self.boolean('validate')

try:
	option = Option(folder=os.path.join('scavenger','dispatch')).option
except OptionError,e:
	print str(e)
	sys.exit(1)

# Debugging

debug_option = not not option.debug & 1

if debug_option:
	option.display()
	print "+"*80

from scavenger.dispatch.server import DispatchFactory

factory = DispatchFactory(option.policy,option.filter,option.action,option.time,option.validate)

from twisted.internet import reactor

reactor.listenUDP(25252, factory.buildProtocol())
reactor.run()
