#!/usr/bin/env python
# encoding: utf-8
"""
server.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

debug = False

from twisted.internet.protocol import DatagramProtocol

from scavenger.policy.message import PolicyMessageFactory
from scavenger.cache import LockedExpirationCache as Cache
from scavenger.message import FactoryError
from scavenger.dispatch.parser import Parser
from scavenger.policy.client import policy_client
from scavenger.tools.ip import toipn
from scavenger.action.client import action_client

class DispatchProtocol(DatagramProtocol):
	debug = True

	def startProtocol(self):
		# be careful self.factory already exists and is the reference to the factory which created us
		self._factory = PolicyMessageFactory()
		self._parser = Parser()
	
	def datagramReceived(self, data, (host, port)):
		control = self._parser.parse(data)
		
		if control is None:
			return

		try:
			postfix = self._factory.fromControl(control)
		except FactoryError,e:
			print 'could not convert the control message'
			print str(e)
			print control
			return

		if postfix['server_address'] in self.factory.getFilters():
			# this spammer was already intercepted by our trap MTA
			return

		client = postfix['client_address']

		if self.factory.getCache().has_key(client):
			# we already notified the action server about this spammer
			return

		host,port = self.factory.getPolicy(client)
		policy_client(host,port,self.dispatch,client,postfix)
	
	def dispatch (self,client,message):
		cmd = message.split(' ')[0]
		if self.debug: print "%-15s %s" % (client,message)
		if cmd == 'DUNNO':
			return
		elif cmd in ['HOLD','FILTER']:
			location = self.factory.getAction(client)
			action_client(location[0],location[1],self.updateCache,client,message)
	
	def updateCache (self,client,boolean):
		if boolean:
			self.factory.getCache()[client] = True

from twisted.internet.protocol import ServerFactory

class DispatchFactory(ServerFactory):
	protocol = DispatchProtocol

	def __init__ (self,policies,filters,action,time):
		self._policies = policies
		self._number = len(policies)
		self._filters = filters
		self._cache = Cache(time)
		self._action = action

	def getPolicy (self,address):
		hash = int(address.split('.')[-1]) % self._number
		return self._policies[hash]

	def getFilters (self):
		# XXX: This is not lock protected so only read access should be done
		return self._filters

	def getCache (self):
		return self._cache

	def getAction (self,client):
		ip = toipn(client)
		for k in self._action.keys():
			start, end = k
			if ip >= start and ip <= end:
				return self._action[k]
		return None

	def buildProtocol (self):
		p = self.protocol()
		p.factory = self
		return p
