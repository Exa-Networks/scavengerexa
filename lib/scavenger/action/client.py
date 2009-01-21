#!/usr/bin/env python
# encoding: utf-8
"""
client.py

Created by Thomas Mangin on 2009-01-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from twisted.internet.protocol import Protocol

class ActionClientProtocol(Protocol):
	def connectionMade (self):
		self.transport.write(self.factory.getMessage())

	def dataReceived(self, data):
		response = data.strip().upper()
		self.factory.processAnswer(response)


from twisted.internet.protocol import ClientFactory

class ActionClientFactory(ClientFactory):
	protocol = ActionClientProtocol

	def __init__(self,callback,client,message):
		self.callback = callback
		self.client = client
		self.message = message

	def processAnswer (self,response):
		self.callback(self.client,True if response == 'OK' else False)
	
	def getMessage (self):
		return "%s %s" %(self.client,self.message)

from twisted.internet import reactor

def action_client (host,port,callback,client,triplet):
	# kv is a dictionary of what postfix send as key=value
	factory = ActionClientFactory(callback,client,triplet)
	reactor.connectTCP(host,port,factory)

