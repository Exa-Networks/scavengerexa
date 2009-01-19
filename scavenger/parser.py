#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from scavenger.message import FactoryError

class Parser (object):
	def __init__ (self,factory,debug):
		self.debug = debug
		self._factory = factory

	def parse (self,data):
		message = {}
		valid = False
		for line in data.split('\n'):
			line = line.strip()
			if self.debug:
				print 'line', line
			if line == '':
				valid = True
				break
			part = line.split('=')
			if len(part) != 2:
				if self.debug:
					print 'invalid line [%s]' % line
				break
			k,v = part
			message[k] = v

		if not valid:
			return None

		try:
			return self._factory.fromDict(message)
		except FactoryError,e:
			print 'message is not valid', str(e)
			if self.debug:
				print message
			return None

