#!/usr/bin/env python
# encoding: utf-8
"""
response.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""


class PluginResponse(Exception):
	type = 'undefined'
	command = ''
	message = ''

# Postfix Response

class PostfixResponse (PluginResponse):
	type = 'postfix'
	web_code = ''

	def __init__ (self,message,delay):
		self.message = message
		self.delay = delay
	
	def __str__ (self):
		return "action=%s %s" % (self.command,self.message)

class ResponseContinue (PluginResponse):
	pass

class ResponseAccept (PostfixResponse):
	command = "OK"

class ResponseFail (PostfixResponse):
	command = "550"

class ResponseTempFail (PostfixResponse):
	command = "450"

class ResponseHold (PostfixResponse):
	command = "HOLD"

class ResponseRedirect (PostfixResponse):
	command = "REDIRECT"

class ResponseDiscard (PostfixResponse):
	command = "DISCARD"

class ResponseFilter (PostfixResponse):
	command = "FILTER"
	destination = "0.0.0.0:00000"

	def __str__ (self):
		return "action=%s [%s] %s" % (self.command,self.destination,self.message)

class ResponsePrepend (PostfixResponse):
	command = "PREPEND"


# Scavenger Response

class ScavengerResponse (PluginResponse):
	duration = 0
	type = 'scavenger'

	def __init__ (self,message,duration=None,destination=None):
		self.message = message
		if duration is not None:
			self.duration = duration
		if destination is not None:
			self.destination = destination

	def __str__ (self):
		return "%s %s (%s) %s" % (self.command,message['client_address'],self.duration,self.message)

class ResponseFilter (ScavengerResponse):
	command = "FILTER"
	# XXX: if the destination is left as this, the dispatcher will have the task of selecting the action backend
	destination = "0.0.0.0:00000"

	def __str__ (self):
		return "%s %s [%s] (%s) %s" % (self.command,message['client_address'],self.destination,self.duration,self.message)

class ResponseBlock (ScavengerResponse):
	command = "HOLD"

# Undetermined

class ResponseUndetermined (PluginResponse):
	type = "generic"
	command = "DUNNO"
	command = "IGNORE"
	delay = 0
	duration = 0

	def __str__ (self):
		if self.type == 'scavenger':
			return 'HAM'
		if self.type == 'postfix':
			return 'action=DUNNO'
		if self.type == 'generic':
			return ''

# Errors

class PluginError(PluginResponse):
	pass

# The plugin occured a problem running and should be skipped
class InternalError(PluginError):
	pass

# The plugin can not provide an answer
class NoResponseError(PluginError):
	pass

# The plugin has a problem with one of its input
class DataError(PluginError):
	pass

# Should not be used by the plugins
class UncheckableError(PluginError):
	pass



