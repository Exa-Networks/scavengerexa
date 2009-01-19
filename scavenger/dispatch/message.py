#!/usr/bin/env python
# encoding: utf-8
"""
message.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from scavenger.message import Message, Factory, FactoryError

class DispatchMessageFactory (Factory):
	_convert_value = {
		'si': lambda _:_,
		'di': lambda _:_,
		'st': lambda _:_,
		'co': lambda c:str(c),
		'he': lambda _:_,
		'se': lambda _:_,
		're': lambda _:_,
		'rc': lambda c:str(c),
		'in': lambda _:_,
	}

	_convert_key = {
		'si':      'source',
		'di': 'destination',
		'st':       'state',
		'co':        'code',
		'he':        'helo',
		'se':      'sender',
		're':   'recipient',
		'rc':       'count',
		'in':    'instance',
	}
	_keys = _convert_key.keys()

        def new (self):
		message = Message()
		message['si'] = ""
		message['di'] = ""
		message['st'] = ""
		message['he'] = ""
		message['se'] = ""
		message['re'] = ""
		message['co'] = 0
		message['rc'] = 0
		message['in'] = self._instance()
		return message
	
	def fromCapture (self,capture):
		try:
			message = Message()
			for k in self._keys:
				ck = self._convert_key[k]
				message[k] = self._convert_value[k](capture[ck])
			return message
		except KeyError,e:
			raise FactoryError(str(e))

	def fromDict (self,control):
		try:
			message = Message()
			for k in self._keys:
				message[k] = control[k]
			return message
		except KeyError,e:
			raise FactoryError(str(e))
