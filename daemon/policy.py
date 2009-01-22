#!/usr/bin/env python
# encoding: utf-8
"""
policy.py

Created by Thomas Mangin on 2007-12-01.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import sys

# Intialise Logging

from twisted.python import log
try:
	log.startLogging(sys.stdout)
except:
	print 'could not initialise twisted logging'

from scavenger.option import Option as BaseOption, OptionError

class Option (BaseOption):
	valid = ('debug','slow','configuration')

	def _configuration (self):
		conf = self._env('configuration')
		if conf.endswith('.conf'):
			self['configuration'] = conf
		else:
			self['configuration'] = 'policy.conf'

try:
	option = Option()
except	OptionError, e:
	print '%s' % str(e)
	sys.exit(1)

debug_option = not not option.debug & 1
        
if debug_option:
	option.display()
	print "+"*80

# Enabling (or not) psycho

if not option['slow']:
	try:
		import psyco
		psyco.full()
		print 'Psyco found and enabled'
	except ImportError:
		print 'Psyco is not available'

# Starting the service

from twisted.application import internet, service
from twisted.internet import protocol, reactor
from twisted.protocols import policies

from scavenger.policy.service import MailPolicyService,PluginError
from scavenger.policy.factory import IMailPolicyFactory

from scavenger.policy.configuration import Configuration,ConfigurationError

configuration = Configuration(option.configuration)
configuration.display()

reactor.suggestThreadPoolSize(configuration['thread'])

application = service.Application('mail policy',uid=1,gid=1)	
serviceCollection = service.IServiceCollection(application)
try:
	mailservice = MailPolicyService(configuration)
except PluginError:
	print 'no plugin match the criteria given, can not start the policy server'
	sys.exit(1)

mailfactory = policies.TimeoutFactory(IMailPolicyFactory(mailservice),timeoutPeriod=configuration['timeout'])

internet.TCPServer(configuration['port'],mailfactory).setServiceParent(serviceCollection)

serviceCollection.startService()
reactor.run()
sys.exit(1)

