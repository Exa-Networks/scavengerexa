#!/usr/bin/env python
# encoding: utf-8
"""
factory.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import time
from zope.interface import Interface, implements
from plugin import response

class IMailPolicyFactory (Interface):
	def policeMessage (message):
		"""returns a list of what the plugin are saying about the message"""
	
	def sanitiseMessage (message):
		"""return what the version of the protocol of the request"""

	def getPlugins (state):
		"""returns a list of plugin which can run at this level"""
	
	def validateMessage (message):
		"""check that the message have the key we need"""

from twisted.python import log
from twisted.internet import protocol
from twisted.internet import defer

from scavenger.policy.protocol import PostfixPolicyProtocol,ScavengerPolicyProtocol
from scavenger.policy.service import IMailPolicyService

message = "[policy server reports] message %(msg)s\ncode %(code)s"

class MailPolicyFactoryFromService (protocol.ServerFactory):
	implements(IMailPolicyFactory)
	
	debug = False
	
	postfix_21 = ['request','protocol_state','protocol_name','helo_name','queue_id','sender','recipient','recipient_count','client_address','client_name','reverse_client_name','instance',]
	postfix_22 = ['sasl_method','sasl_username','sasl_sender','size','ccert_subject','ccert_issuer','ccert_fingerprint',]
	postfix_23 = ['encryption_protocol','encryption_cipher','encryption_keysize','etrn_domain',]
	postfix_25 = ['stress',]

	scavenger_10 = ['server_address','code','origin']
	
	states = ['VRFY','ETRN','CONNECT','EHLO','HELO','MAIL','RCPT','DATA','END-OF-DATA',]
	
	def __init__ (self,service):
		if service.getType() == 'scavenger':
			self.protocol = ScavengerPolicyProtocol
		elif service.getType() == 'postfix':
			self.protocol = PostfixPolicyProtocol 
		else:
			raise ValueError('unknow protocol option (scavenger,postfix)')

		log.msg('+'*80)
		self.plugins = {}
		self.service = service
		self.template = self.service.configuration.get('message',message)
		self.type = self.service.getType()
		self.version = {'postfix':{},'scavenger':{}}
		
		for kv,ver in ((self.postfix_21,'2.1'),(self.postfix_22,'2.2'),(self.postfix_23,'2.3'),(self.postfix_25,'2.5')):
			for k in kv:
				self.version['postfix'][k] = ver

		for kv,ver in ((self.postfix_21,'2.1'),(self.scavenger_10,'1.0')):
			for k in kv:
				self.version['scavenger'][k] = ver

		for state in self.states:
			self.plugins[state] = []

		for plugin in self.service.getPlugins():
			states = plugin.getStates()
			for state in states:
				self.plugins[state].append(plugin)

	def getPlugins (self,message):
		protocol = message['request']
		state = message['protocol_state']
		for plugin in self.plugins[state]:
			yield plugin

	def policeMessage (self,message):
		self._storeMessage(message)
		response = self._checkMessage(message)
		print "%-15s %4s : %s" % (message['client_address'],message['protocol_state'],str(response))
		return response

	def _storeMessage (self,message):
		# Perform database storage functions
		for plugin in self.getPlugins(message):
			try:
				plugin.store(message)

			# Errors

			except response.InternalError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'plugin had an internal error',str(r)))
				continue
			except response.DataError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'the plugin does not like the data provided',str(r)))
				continue
			except response.UncheckableError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'uncheckable',str(r)))
				continue
			except response.NoResponseError, r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'no answer from the plugin',str(r)))
				continue

			# Uncaught Exception

			except response.PluginError,r:
				log.msg('plugin %s : %s' % (plugin.getName(),'no reponse'))
				continue
			except Exception, r:
				log.msg('plugin %s : %s' % (plugin.getName(),'unknown response '+str(r)))
				continue

	def _checkMessage (self,message):
		# Run all the plugin in order and act depending on the response returned
		for plugin in self.getPlugins(message):
			if self.debug: log.msg('running pluging ' + plugin.getName())

			try:
				r = plugin.police(message)
			except Exception, e:
				if plugin.debug:
					import traceback
					traceback.print_exc()
				else:
					log.msg("Plugin %s is raising an error - %s %s" % (plugin.getName(),str(type(e)), e.message))
				continue

			try:
				raise r

			# Nothing can be said about the data

			except response.ResponseContinue:
				if self.debug: log.msg('plugin %s : %s' % (plugin.getName(),'continue'))
				continue

			# Allow or Block the mail

			except response.PostfixResponse, r:
				# XXX: Need to create a dict class which reply '' to every unknown key 
				log.msg('plugin %s : %s' % (plugin.getName(),r.message))
				if r.delay: log.msg('plugin %s : forcing a time of %d' % (plugin.getName(), r.delay))
				return r

			except response.ScavengerResponse, r:
				# XXX: Need to create a dict class which reply '' to every unknown key 
				log.msg('plugin %s : %s' % (plugin.getName(),r.message))
				if r.duration: log.msg('plugin %s : forcing a duration of %d' % (plugin.getName(), r.duration))
				return r

			# Nothing can be said about the data

			except response.ResponseContinue:
				log.msg('plugin %s : %s' % (plugin.getName(),'continue'))
				continue

			# Errors

			except response.InternalError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'plugin had an internal error',str(r)))
				continue
			except response.DataError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'the plugin does not like the data provided',str(r)))
				continue
			except response.UncheckableError,r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'uncheckable',str(r)))
				continue
			except response.NoResponseError, r:
				log.msg('plugin %s : %s (%s)' % (plugin.getName(),'no answer from the plugin',str(r)))
				continue

			# Uncaught Exception

			except response.PluginError,r:
				log.msg('plugin %s : %s' % (plugin.getName(),'no reponse'))
				continue
			except Exception, r:
				log.msg('plugin %s : %s' % (plugin.getName(),'unknown response '+str(r)))
				continue

		if self.debug: log.msg('plugins could not say anything about this message')
		return response.ResponseUndetermined(self.type)

	def sanitiseMessage (self,message):
		r = {}
		for k in self.version[self.type].keys():
			if not message.has_key(k):
				r[k]=''
			else:
				r[k] = message[k]
		then = time.time()
		if message.has_key('timestamp'):
			try:
				then = float(message['timestamp'])
			except (TypeError, ValueError):
				pass

		r['timestamp'] = int(then)
		return r
	
	def validateMessage (self,message):
		for k in ['client_address','protocol_state']:
			if not message.has_key(k):
				return False

		if message['protocol_state'] not in self.states:
			log.msg('invalid protocol state %s' % message['protocol_state'])
			return False

		if message['request'] not in ['smtpd_access_policy','scavenger_access_policy']:
			log.msg('invalid request type %s' % message['request'])
			return False

		if message['request'] != 'scavenger_access_policy':
			return True

		for k in ['server_address','code','origin']:
			if not message.has_key(k):
				log.msg('scavenger message must have key %s' % k)
				return False

		return True




from twisted.python import components

components.registerAdapter(MailPolicyFactoryFromService,
                           IMailPolicyService,
                           IMailPolicyFactory)
