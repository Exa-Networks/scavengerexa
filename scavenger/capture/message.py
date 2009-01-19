#!/usr/bin/env python
# encoding: utf-8
"""
message.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from scavenger.message import Message, Factory, FactoryError

TypeBool = type(True)
TypeString = type('')
TypeInt = type(0)
TypeLong = type(0L)

class CaptureMessageFactory (Factory):
	def __init__ (self,origin):
		Factory.__init__(self)
		self._origin = origin

	def _check(self,tc,td,k,v):
		if tc != td:
			raise FactoryError('key \'%s\' is of %s not of %s "%s"' % (k,str(tc),str(td),str(v)))

	def new (self):
		message = Message()
		message['skip'] = False
		message['state'] = ""
		message['helo'] = ""
		message['sender'] = ""
		message['recipient'] = ""
		message['source'] = ""
		message['destination'] = ""
		message['code'] = 0
		message['count'] = 0
		message['instance'] = self._instance()
		message['origin'] = self._origin
		return message

	def fromDict (self,msg):
		message = Message()
		for k,v in msg.iteritems():
			t = type(v)
			if k in ['skip']:
				self._check(t,TypeBool,k,v)
			elif k in ['state']:
				self._check(t,TypeString,k,v)
				v = v.upper()
				if v and v not in ['HELP','HELO','EHLO','VRFY','ETRN','RSET','AUTH','MAIL','RCPT','DATA','END-OF-DATA','QUIT']:
					raise FactoryError('not a valide state "%s"' % str(v))
			elif k in ['source','destination']:
				self._check(t,TypeString,k,v)
				p = v.split('.')
				if p.count(':'):
					raise FactoryError('this code is ipv4 only "%s"' % v)
				if len(p) != 4:
					raise FactoryError('not a valid IP "%s"' % v)
				for n in p:
					if not n.isdigit():
						raise FactoryError('not a valid IP "%s"' % v)
			elif k in ['count']:
				if t == TypeString:
					if v.isdigit():
						v = int(v)
					else:
						self._check(t,TypeInt,k,v)
				else:
					self._check(t,TypeInt,k,v)
			elif k in ['code']:
				if t == TypeString:
					if v.isdigit():
						v = int(v)
					else:
						self._check(t,TypeInt,k,v)
				else:
					self._check(t,TypeInt,k,v)
				if v < 0 or v >= 600:
					raise FactoryError('the number can not be a SMTP code "%s"' % str(v))
			elif k in ['sender','recipient']:
				self._check(t,TypeString,k,v)
				v = v.lower()
				if v and v.count('@') != 1:
					raise FactoryError('invalid email address "%s"' % str(v))
			else:
				self._check(t,TypeString,k,v)
			message[k] = v
		return message

