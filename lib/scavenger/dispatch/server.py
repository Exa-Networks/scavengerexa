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

from scavenger.tools.ip import source_hash, toipn
from scavenger.cache import LockedExpirationCache as Cache
from scavenger.capture.message import CaptureMessageFactory
from scavenger.parser import Parser
from scavenger.policy.client import policy_client
from scavenger.action.client import action_client

class DispatchProtocol(DatagramProtocol):
	debug = True

	def startProtocol(self):
		if self.factory.validateUDP():
			self._parser = Parser(CaptureMessageFactory())
		else:
			self._parser = Parser()
		self._id = 0
	
	def datagramReceived(self, data, (host, port)):
		id = self._id
		self._id += 1

		message = self._parser.parse(data)
		
		if message is None:
			return

		if message['di'] in self.factory.getFilters():
			# this spammer was already intercepted by our trap MTA
			return

		client = message['si']

		if self.factory.getCache().has_key(client):
			# we already notified the action server about this spammer
			return

		host,port = self.factory.getPolicy(client)
		if self.debug: print "[%7s] %-15s dispatching message to %s:%s" % (id,client,host,port)
		policy_client(host,port,self.dispatch,id,client,message)
	
	def dispatch (self,id,client,message):
		cmd = message.split(' ')[0]
		if self.debug: print "[%7s] %-15s policy answers %s" % (id, client,message)
		if cmd == 'HAM':
			return
		elif cmd in ['HOLD','FILTER']:
			for location in self.factory.getActions(client):
				action_client(location[0],location[1],self.updateCache,client,message)
	
	def updateCache (self,client,boolean):
		if boolean:
			self.factory.getCache()[client] = True

from twisted.internet.protocol import ServerFactory

class DispatchFactory(ServerFactory):
	protocol = DispatchProtocol

	def __init__ (self,policies,filters,action,time,validate):
		self._policies = policies
		self._filters = filters
		self._cache = Cache(time)
		self._action = action
		self._validate = validate

	def validateUDP (self):
		return self._validate

	def getPolicy (self,address):
		return source_hash(address,self._policies)

	def getFilters (self):
		# XXX: This is not lock protected so only read access should be done
		return self._filters

	def getCache (self):
		return self._cache

	def getActions (self,client):
		ip = toipn(client)
		for k in self._action.keys():
			start, end = k
			if ip >= start and ip <= end:
				for action in self._action[k]:
					yield action
		raise StopIteration()

	def buildProtocol (self):
		p = self.protocol()
		p.factory = self
		return p

