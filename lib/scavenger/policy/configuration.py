#!/usr/bin/env python
# encoding: utf-8
"""
configuration.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import sys

class ConversionError (Exception):
	pass

def is_python_key (key):
	if len(key) == 0:
		return False
	
	letter = key[0]
	if not letter.isalpha() and not letter in "_":
		return False
	
	for letter in key[1:]:
		if not letter.isalnum() and not letter[0] in "_":
			return False
	
	return True

def python_type (value,strict=True):
	if value == 'None': return None			
	
	try: return to_numeric(value)
	except ConversionError, e: pass
	
	try: return to_truefalse(value)
	except ConversionError, e: pass
	
	try: return to_string(value)
	except ConversionError,e: pass

	if strict: raise ConversionError('Unknown python type [%s]' % str(value))
	
	return value

def to_string (value):
	if len(value) < 2:
		raise ConversionError('too short to be a string')
	
	separator = ['"',"'"]
	count = 0
	
	while value[0] in separator and value[0] == value [-1]:
		separator = [value[0]]
		value = value[1:-1]
		count +=1
		if value == '':
			break
	
	if count == 1 or count == 3:
		return value
	
	raise ConversionError("not a string [%s] we found %d separator %s" % (str(value),count,str(separator)))

def is_string (value):
	try:
		to_string(value)
		return True
	except ConversionError, e:
		return False

def to_unquoted_string (value):
	try: return to_string(value)
	except ConversionError, e: return value

def is_truefalse (value):
	return value in ['True', 'False']

def to_truefalse (value):
	try:
		tf = {'True':True,'False':False}
		return tf[value]
	except KeyError, e:
		raise ConversionError('not True or False')

def to_boolean (value):
	try: return to_truefalse(value)
	except ConversionError, e: pass
	
	n = to_numeric(value)
	if n: return True
	else: return False

def to_numeric (value):
	try: return int(value)
	except ValueError, e: pass
	
	try: return long(value)
	except ValueError, e: raise ConversionError('not a number [%s]' % str(value))

def to_duration (value):
	_multiplier = {'m':60, 'h':60*60, 'd':60*60*24}
	multiply = 1
	
	try:
		m = value[-1]
		if _multiplier.has_key(m):
			return _multiplier[m]*int(value[:-1])
		return int(value)
	except IndexError, e:
		raise ConversionError('no a duration')
	except ValueError, e:
		raise ConversionError('no a duration')
	
class ConfigurationError (Exception):
	pass

class Configuration (dict):
	debug = False
	
	convert = {
		'debug ' : lambda _:_,
		'timeout ' : lambda _:_,
		'ip ' : lambda _:_,
		'port ' : lambda _:_,
		'acl' : lambda _: [r for r in _.split(' ') if r != ''],
		'type' : lambda _:_,
		'thread' : lambda _:_,
		'database_host' : lambda _:_,
		'database_port' : lambda _:_,
		'database_user' : lambda _:_,
		'database_password' : lambda _:_,
		'database_path' : lambda _:_,
		'database_prefix' : lambda _:_,
		'states' : lambda _: [r for r in _.split(' ') if r != ''],
		'plugins' : lambda _: [r for r in _.split(' ') if r != ''],
		'message' : lambda _:_,
	}

	def __init__ (self,name):
		dict.__init__(self)

		self.etc = os.environ.get('ETC','/etc')
		self.cache = os.environ.get('CACHE','/var/cache')
		
		self.configuration = os.path.join(self.etc,'scavenger','policy',name)
		self.line = ""
		self.number = 0

		self.number = 0
		with open(self.configuration,'r') as f:
			for line in f.readlines():
				self.number += 1
				self.line = line

				line = line.strip()
				if line == "":
					continue
				if line[0] == '#':
					continue

				try:
					key,value = line.split('=',1)
				except ValueError:
					continue

				key = key.strip()
				value = python_type(value.strip())

				if key in self.convert.keys():
					self[key] = self.convert[key](value)
				else:
					self[key] = value
		
	def display (self):
		print "*"*80
		print 'configuration is', self.configuration
		for k,v in self.iteritems():
			print "  * %-15s = %s" % (k,v)
