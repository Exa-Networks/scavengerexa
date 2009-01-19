#!/usr/bin/env python
# encoding: utf-8
"""
message.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
"""

from scavenger.message import Message, Factory, FactoryError
from scavenger.tools.ip import toipn,toips

class PolicyMessageFactory (Factory):
	_postfix_21 = {
		'request' : 'scavenger_access_policy',
		'protocol_name' :              'SMTP',
		'queue_id' :                       '',
		'reverse_client_name' :            '',
	}

	_convert_key = {
		'si' : 'client_address',
		'di' : 'server_address',
		'st' : 'protocol_state',
		'co' :           'code',
		'he' :      'helo_name',
		'se' :         'sender',
		're' :      'recipient',
		'rc' :          'count',
		'in' :       'instance',
	}

	_convert_value = {
		'si' : lambda s,v:str(v),
		'di' : lambda s,v:str(v),
		'st' : lambda s,v:str(v),
		'co' : lambda s,v:str(v),
		'he' : lambda s,v:str(v),
		'se' : lambda s,v:str(v),
		're' : lambda s,v:str(v),
		'rc' : lambda s,v:str(v),
		'in' : lambda s,v:str(v),
	}

	short = _convert_key.keys()

	def fromControl (self,msg):
		for k in self.short:
			if not k in msg:
				raise FactoryError ('missing key [%s]' % k)

		message = Message()
		message.update(self._postfix_21)

		for k in self.short:
			message[self._convert_key[k]] = self._convert_value[k](self,msg[k])
		return message

