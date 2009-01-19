#!/usr/bin/env python
# encoding: utf-8
"""
client.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from twisted.internet.protocol import Protocol

class PostfixPolicyClientProtocol(Protocol):
	def connectionMade (self):
		self.transport.write(self.factory.getMessage())

	def dataReceived(self, data):
		data = data.strip()
		if not data.count('='):
			return
		action,response = data.split('=',1)
		if action.lower() != 'action':
			return
		self.factory.processAnswer(response)


from twisted.internet.protocol import ClientFactory

class PostfixPolicyClientFactory(ClientFactory):
	protocol = PostfixPolicyClientProtocol

	def __init__(self,callback,id,client,message):
		self.id = id
		self.callback = callback
		self.client = client
		self.message = message

	def processAnswer (self,response):
		self.callback(self.id,self.client,response)
	
	def getMessage (self):
		return str(self.message)


from twisted.internet import reactor

def policy_client (host,port,callback,id,client,kv):
	# kv is a dictionary of what postfix send as key=value
	factory = PostfixPolicyClientFactory(callback,id,client,kv)
	reactor.connectTCP(host,port,factory)

