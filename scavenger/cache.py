#!/usr/bin/env python
# encoding: utf-8
"""
cache.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
"""

from __future__ import with_statement

import time
from threading import Lock

# XXX: This should really be using memcached to prevent memory exhaustion but I am a lazy bee
# XXX: Do you feel like converting the code to it please ? :D

class ExpirationCache (dict):
	def __init__ (self,ttl,debug=False):
		self.debug = debug
		self.timed = {}
		self.ttl = ttl
		self.next = int(time.time()) + ttl

	def __getitem__ (self,key):
		return dict.__getitem__(self,key)

	def __setitem__ (self,key,value,ttl=None):
		if ttl == None:
			ttl = self.ttl
		t = int(time.time())

		if self.next < t:
			self.next += self.ttl
			print 'cache cleanup: time is %d next run at %d' % (t, self.next)
			r = []
			if self.debug:
				print 'total key #', len(self.keys())
			for k,v in self.timed.iteritems():
				if v < t:
					r.append(k)
			if self.debug:
				print 'cache cleanup: purging key #', len(r)
			for k in r:
				if self.debug:
					print 'cache cleanup: expiring key', str(k)
				del self[k]
		self.timed[key] = t + self.ttl
		return dict.__setitem__(self,key,value)

	def __delitem__ (self,key):
		del self.timed[key]
		dict.__delitem__(self,key)

class LockedExpirationCache (dict):
	def __init__ (self,ttl,debug=False):
		self.debug = debug
		self.timed = {}
		self.ttl = ttl
		self.next = int(time.time()) + ttl
		self.lock = Lock()


	def __getitem__ (self,key):
		with self.lock:
			return dict.__getitem__(self,key)

	def __setitem__ (self,key,value,ttl=None):
		if ttl == None:
			ttl = self.ttl
		t = int(time.time())

		with self.lock:
			if self.next < t:
				self.next += self.ttl
				print 'cache cleanup: time is %d next run at %d' % (t, self.next)
				r = []
				if self.debug:
					print 'total key #', len(self.keys())
				for k,v in self.timed.iteritems():
					if v < t:
						r.append(k)
				if self.debug:
					print 'cache cleanup: purging key #', len(r)
				for k in r:
					if self.debug:
						print 'cache cleanup: expiring key', str(k)
					del self[k]
			self.timed[key] = t + self.ttl
			return dict.__setitem__(self,key,value)

	def __delitem__ (self,key):
		with self.lock:
			del self.timed[key]
			dict.__delitem__(self,key)

