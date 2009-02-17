#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

import imaplib
import poplib

from scavenger.tools.ip import toips,toipn,tostartend
from scavenger.capture.message import Message
from scavenger.capture.message import CaptureMessageFactory, FactoryError

class Parser (object):
	def __init__ (self,proto,server,user,password,filter="(ALL)"): # "(NEW)"
		if not proto in ['pop','imap']:
			raise # XXX: Must raise something intelligent
		self.proto = proto
		self.user = user
		self.password = password
		self.server = server
		self.filter = filter
		if proto == 'pop':
			self.parse = self._parse_pop
		else:
			self.parse = self._parse_imap
		self.factory = CaptureMessageFactory('fbl')
	
	def _parse_imap (self):
		server = imaplib.IMAP4(self.server)
		server.login(self.user,self.password)
		server.select()
		r, data = server.search(None,self.filter)
		if r != 'OK':
			print 'Can not get IMAP mail'
			raise StopIteration()
		for num in data[0].split():
			t,mail = server.fetch(num,'(RFC822)')
			yield self._parse_mail(mail[0][1].split('\n'))
			server.store(num, '+FLAGS', '\\Deleted')
		server.expunge()
		server.close()
		server.logout()
		raise StopIteration()

	def _parse_pop (self):
		server = poplib.POP3(self.server)
		server.user(self.user)
		server.pass_(self.password)
		response,nums,_ = server.list()
		if not response.startswith(response):
			print 'Can not get POP mail'
			raise StopIteration()
		for num in nums:
			message = server.retr(num)[1]
			yield self._parse_mail(message)
			server.dele(num)
		server.quit()
		raise StopIteration()

	def _parse_mail (self,mail):
		skip = True
		message = self.factory.new()
		for line in mail:
			if line.startswith('Feedback-Type: abuse'):
				skip = False
			if skip: continue
			
			line = line.strip()
			if not line:
				break
			
			key,value = line.split(':',1)
			key = key.lower().strip()
			value = value.lower().strip()
			if key == 'version':
				if value != '0.1':
					print 'Unknown version of the FBL'
					return StopIteration()
			if key == 'source-ip':
				message['si'] = value
			
		if not message['si']:
			return StopIteration()
		
		return message
	