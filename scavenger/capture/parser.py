#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from scavenger.tools.ip import toips,toipn,tostartend
from scavenger.capture.message import Message
from scavenger.capture.message import CaptureMessageFactory, FactoryError

class Parser (object):
	def __init__ (self,cache,cidrs,debug):
		self._factory = CaptureMessageFactory('pcap')
		self.debug = debug

		self._internal = []
		for cidr in cidrs:
			self._internal.append(tostartend(cidr))
		self._cache = cache

		self.ip = '0.0.0.0'
		self.port = 0

	def __log (self,s):
		if self.debug:
			print "'%-15s:%5s " % (self.ip,self.port), s

	def __email (self,line):
		try:
			email = line.split(':',1)[1].strip()
			email = email.split('>',1)[0]
			if email.count('<'):
				email = email[email.index('<')+1:]
			return email
		except IndexError:
			self.__log('could not parse [%s] for email' % line.strip())
			return 'invalid@email'

	def __pipelined (self):
		# the client is pipelining and we will send something to the control server about it
		# as the code is not cleaver enough to parse pipelined mail
		self.__log('pipelining')
		return None

	def internal (self,ip):
		for start,end in self._internal:
			if ip >= start and ip <= end:
				return True
		return False

	def command (self,data):
		k = "%s:%s" % (self.ip,self.port)
		parsed = False

		if self._cache.has_key(k):
			cache = self._cache[k]
			if cache['skip']:
				self.__log('skipping payload')
				# update the key so it does not expire
				cache['skip'] = True
				return None
		else:
			cache = None

		for line in data.split('\n'):
			invalid = False
			try:
				cmd = line[:4].upper()
			except IndexError:
				if cache is None:
					self.__log('invalid command [%s]' % ''.join([c for c in str(line)[:4] if c.isalnum()]))

					cache = self._factory.new()
					cache['source'] = toips(self.si)
					cache['destination'] = toips(self.di)
					cache['state'] = ''
					cache['skip'] = True

					self._cache[k] = cache 
				return None

			if cmd not in ['HELP','HELO','EHLO','VRFY','ETRN','RSET','AUTH','MAIL','RCPT','DATA','QUIT']:
				if cache is None:
					self.__log('invalid command [%s]' % ''.join([c for c in str(line)[:4] if c.isalnum()]))

					cache = self._factory.new()
					cache['source'] = toips(self.si)
					cache['destination'] = toips(self.di)
					cache['state'] = ''
					cache['skip'] = True

					self._cache[k] = cache
				return None

			if cmd == 'QUIT':
				if not cache is None:
					del self._cache[k]
				continue
			
			if parsed:
				return self.__pipelined()
			parsed = True

			if cmd in ['RSET','HELO','EHLO']:
				self.__log('creating %s tracking' % cmd)

				cache = self._factory.new()
				cache['source'] = toips(self.si)
				cache['destination'] = toips(self.di)
				cache['state'] = cmd
				cache['helo'] = line[4:].strip()

				self._cache[k] = cache
				continue

			if cache is None:
				if cmd == 'MAIL':
					cache = self._factory.new()
					cache['source'] = toips(self.si)
					cache['destination'] = toips(self.di)
				else:
					self.__log('no command tracking')
					continue

			cache['state'] = cmd

			if cmd in ['HELP','VRFY','ETRN','AUTH']:
				continue

			if cmd == 'MAIL':
				# <> becomes an empty sender
				cache['sender'] = self.__email(line)
				cache['recipient'] = ""
				cache['count'] = 0
				continue

			if cmd == 'RCPT':
				cache['recipient'] = self.__email(line)
				cache['count'] += 1
				continue

			if cmd == 'DATA':
				continue

		return None


	def response (self,data):
		k = "%s:%s" % (self.ip,self.port)

		if not k in self._cache:
			self.__log('untracked command response')
			return None

		cache = self._cache[k]
		if cache['skip']:
			self.__log('set to start reading command')
			cache['skip'] = False
			if cache['state'] == 'DATA':
				cache['state'] = 'END-OF-DATA'
		else:
			if cache['state'] == 'DATA':
				cache['skip'] = True

		line = data.split('\n')[0]
		if len(line) < 5:
			return None
		
		sep = line[3]
		if not sep in ['-',' ']:
			return None
		
		code = line[:3]
		if not code.isdigit():
			self.__log('invalid code returned [%s]' % code)
			return None

		self.__log('response is [%s]' % code)
		cache['code'] = code

		if cache['state'] in ['HELO','EHLO','MAIL','RCPT','DATA','END-OF-DATA']:
			return cache
		self.__log('skipping answer for unmonitored state %s' % cache['state'])
		return None

	def select (self,si,sp,di,dp):
		self.si = si
		self.di = di

		if self.internal(si) and dp == 25:
			self.ip = si
			self.port = sp
			self.function=self.command
		elif self.internal(di) and sp == 25:
			self.ip = di
			self.port = dp
			self.function=self.response
		else:
			self.ip = '0.0.0.0'
			self.port = 0
			self.function=lambda x: None

		return self

	def parse (self,data):
		# XXX: we assume that we can not see customer to customer mail here 

		data = data.strip()
		if not data:
			self.__log('empty payload')
			return None

		capture = self.function(data)

		if capture is None:
			return None

		try:
			return self._factory.fromDict(capture)
		except FactoryError,e:
			raise

