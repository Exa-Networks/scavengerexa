#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from imaplib import *

from scavenger.tools.ip import toips,toipn,tostartend
from scavenger.capture.message import Message
from scavenger.capture.message import CaptureMessageFactory, FactoryError

class Parser (object):
	def __init__ (self,server,user,password,filter="(ALL)"): # "(NEW)"
		self.filter = filter
		self.server = IMAP4(server)
		self.server.login(user,password)

	def __del__ (self):
		self.server.logout()

	def parse (self):
		self.server.select()
		r, data = self.server.search(None,self.filter)
		if r != 'OK':
			raise # XXX: ....
		for num in data[0].split():
			t,mail = self.server.fetch(num,'(RFC822)')
			print t
			if mail:
				for line in mail[0][1].split('\n'):
					if line.startswith('X-AOL-INRLY'):
						yield line.split('[')[1].split(']')[0]
		self.server.close()
