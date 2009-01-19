#!/usr/bin/env python
# encoding: utf-8
"""
protocol.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from twisted.internet import reactor,defer
from twisted.python import log
from twisted.protocols import basic

class MailPolicyProtocol(basic.LineReceiver):
	debug = True
	errorReturn = {'error': ('dunno', None), 'connection': ('dunno', None)}
	sanitise = {'protocol_state': lambda s: s.strip().upper()}
	delimiter = '\n'

	def connectionMade (self):
		self.action = {}
	
	def _answer (self,answer):
		log.msg('%s' % answer.strip())
		self.transport.write(answer + '\n\n')
		self.transport.loseConnection()
	
	def response_postfix(self,string):
		self._answer('%s' % string)

	def response_scavenger(self,string):
		self._answer('%s' % string)

	def problem (self,reason = ''):
		self._answer('DEFER_IF_PERMIT Service temporary unavailable (%s)' % reason)

	def lineReceived (self,line):
		try:
			key,value = line.split('=',1)
			key = key.strip().lower()
			self.action[key] = self.sanitise.get(key,lambda s: s.strip())(value)
			return
		except ValueError, e:
			if line.strip() != '':
				log.msg('client %s is not following the protocol' % self.transport.getPeer().host)
				self.problem('invalid line, closing connection [%s]' % line.replace('\n','').replace('\r',''))
				return
			if len(self.action) == 0:
				log.msg('client %s sent an empty line as first line' % self.transport.getPeer().host)
				self.problem('invalid empty line, closing connection [%s]' % line.replace('\n','').replace('\r',''))
				return
		
		if self.debug:
			keys = ['client_address','protocol_state','sender','recipient']
			log.msg(", ".join(["%s" % self.action[k] for k in keys if self.action.has_key(k)]))

		message = self.factory.sanitiseMessage(self.action)
		
		if not self.factory.validateMessage(message):
			log.msg('client %s sent an invalid request' % self.transport.getPeer().host)
			self.problem('problem with the policy message')
			return
			
		#if self.debug:
		#	log.msg("received:\n"+"\n".join(["%s:%s" % (k,v) for k,v in message.iteritems()]))
		#else:
		#	log.msg("received:\n"+"\n".join(["%s:%s" % (_k,_v) for _k,_v in [(k,v) for k,v in message.iteritems() if k in ('protocol_state','client_address','sender','recipient')]]))
		
		d = defer.Deferred()
		d.addCallback(self.factory.policeMessage)
		d.addCallback(self.sendResponse)

		reactor.callInThread(d.callback, message)

	def sendResponse(self, answer):
		if answer.type not in ['postfix','scavenger']:
			# XXX: Should we overload the protocol creation factory to have this locally, or make it an API call ..
			answer.type = self.factory.type
		if answer.type == 'postfix':
			self.sendPostfixResponse(answer)
		if answer.type == 'scavenger':
			self.sendScavengerResponse(answer)
	
	def sendPostfixResponse (self,answer):
		delay = int(answer.delay)
		string = str(answer)

		d = defer.Deferred()
		d.addCallback(self.response_postfix)

		reactor.callFromThread(lambda _args: reactor.callLater(delay, d.callback, _args), string)

	def sendScavengerResponse (self,answer):
		string = str(answer)

		d = defer.Deferred()
		d.addCallback(self.response_scavenger)

		reactor.callFromThread(lambda _args: reactor.callLater(0, d.callback, _args), string)

