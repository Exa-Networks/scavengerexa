#!/usr/bin/env python
# encoding: utf-8
"""
message.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from time import time
from random import randint

class FactoryError (Exception):
	pass

class Message (dict):
	def __str__ (self):
		return '\n'.join(['%s=%s' % (k,v) for (k,v) in self.iteritems()]) + '\n\n'

class Factory (object):
	# XXX: To double check, this is not exactly thread safe but for our use it is not an issue
	__instance = 0

	def __init__ (self):
		self.__instance += 1
		self._inst = self.__instance
		self._rand = randint(0,0xffff)
		self._prefix = "%02x.%04x" % (self._inst,self._rand)

        def _instance (self):
		t = "%02x" % ((int(time()*100)) & 0xff)
		r = "%04x" % randint(0,0xffff)
		return "%s.%s.%s" % (self._prefix,t,r)

	def new (self):
		return Message()

        def copy (self,msg):
		message = Message()
		message.update(msg)
		return message

	def duplicate (self,msg):
		message = self.copy(msg)
		message['instance'] = self._instance()
		return message

