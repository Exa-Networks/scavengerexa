#!/usr/bin/env python
# encoding: utf-8
"""
action-mail.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

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

from scavenger.action.option import Option,OptionError

try:
        option = Option(os.path.join('scavenger','action-mail'), ('debug','port','smarthost','sender','recipient','timeout')).option
except OptionError, e:
        print str(e)
        sys.exit(1)

# Debugging

debug_option = not not option.debug & 1
debug_sending = not not option.debug & 2
debug_protocol = not not option.debug & 4

if debug_option:
	option.display()
	print "no mail sending", debug_sending
	print "debug protocol ", debug_protocol
	print "+"*80

import socket
import smtplib
from scavenger.action.protocol import ActionProtocol

class MailProtocol (ActionProtocol):
	debug = debug_protocol
	def run (self,ip,action,destination,duration,message):
		if debug_sending:
			print 'no email sent in debug mode'
			return
		subject = 'action required to stop a spammer'
		body  = 'scavengerEXA reports that IP %s needs to be %sed for a duration of %s' % (ip,action.lower(),duration)
		if destination:
			body += ' to %s' % destination
		body += '\nfor the following reason :\n\n%s' % message
		message = """\
From: %s
To: %s
Subject: %s

%s""" % (option.sender,option.recipient,subject,body)
		try:
			smtp = smtplib.SMTP(option.smarthost,25,socket.gethostname())
			#smtp.set_debuglevel(1)
			smtp.sendmail(option.sender,option.recipient,message)
			smtp.close()
			return True
		except Exception, e:
			return False


from twisted.internet import protocol

class MailFactory (protocol.Factory):
	protocol = MailProtocol
	
from twisted.application import internet, service
from twisted.internet import reactor
from twisted.protocols import policies

application = service.Application('mail-action')
serviceCollection = service.IServiceCollection(application)

factory = policies.TimeoutFactory(MailFactory(),timeoutPeriod=option.timeout)
internet.TCPServer(option.port, factory).setServiceParent(serviceCollection)

serviceCollection.startService()
reactor.run()
sys.exit(1)

