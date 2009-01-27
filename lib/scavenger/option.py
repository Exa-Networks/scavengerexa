#!/usr/bin/env python
# encoding: utf-8
"""
option.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import os
import sys
import optparse
import socket
from scavenger.tools.ip import toipn

class OptionError (Exception): pass

# add a assign ?? function to use in all the place where self[...] =  is used

class _Option (dict):
	def __getattribute__ (self, key):
		try:
			return dict.__getattribute__(self,key)
		except AttributeError:
			pass
		try:
			return dict.__getitem__(self,key)
		except KeyError,e:
			raise AttributeError(str(e))

	def display (self):
		print "*"*80
		for option in self.keys():
			print "%-20s : %s" %(option, self[option])
		print "*"*80

class Option (object):
	valid = ['debug',]

	def __init__ (self,folder='',options=()):
		self.etc = os.environ.get('ETC','/etc')
		self.cache = os.environ.get('CACHE','/var/cache')
		
		self.__path = os.path.join(self.etc,folder)
		self.__folder = folder 
		self.__options = set(options) if len(options) else self.valid
	
		self.raw = {}
		self.option = _Option()

		self.__reload()

	def __reload(self):
		self.raw.clear()
		self.option.clear()
		
		parser = optparse.OptionParser()
		for option in self.__options:
			parser.add_option('','--%s' % option,action="store",type="str")
		opts,_ = parser.parse_args()
		
		for option in self.__options:
			if getattr(opts,option) != None:
				self.raw[option.lower()] = getattr(opts,option)
				continue
			if os.environ.has_key(option):
				value = os.environ.get(option)
				value.strip()
				self.raw[option.lower()] = value
				continue
			fname = os.path.join(self.__path,option)
			if os.path.isfile(fname):
				lines = []
				with open(fname,'r') as reader:
					for line in reader.readlines():
						line = line.strip()
						if line == '' or line[0] == '#':
							continue
						lines.append(line)
				self.raw[option.lower()] = ' '.join(lines)
				continue
			self.raw[option.lower()] = None
		
		for option in self.__options:
			func = getattr(self,'option_%s' % option)
			func()
	
	def get (self,key):
		return self.raw.get(key.lower(),'')

	def list (self,key):
		self._set(key,self._list(key))

	def _list (self,key):
		return [value for value in self.get(key).split(' ') if value]

	def has (self,key):
		return self.raw.has_key(key.lower())

	def set (self,key):
		self._set(key,self.get(key))

	def _set (self,key,value):
		self.option[key] = value

	def boolean (self,name):
		self._set(name,self._boolean(name,self.get(name)))

	def _boolean (self,name,value):
		if value.lower() in ['true','yes']:
			return True
		if value.lower() in ['false','no']:
			return False
		if value.isdigit():
			return not not value
		raise OptionError('option %s the parameter is not a boolean' % name)
	
	def number (self,name,low=None,high=None):
		self._set(name,self._number(name,self.get(name),low,high))

	def _number (self,name,value,low=None,high=None):
		if not value.isdigit():
			raise OptionError('option %s is not an number' % name)
		value = long(value)
		if low is not None and value < low:
			raise OptionError('option %s is too low (value %d < %d)' % (name,value,low))
		if high is not None and value > high:
			raise OptionError('option %s is too high (value %d > %d)' % (name,value,high))
		return int(value)
	
	def ip (self,name):
		self._set(name,self._ip(self.get(name)))

	def _ip (self,name,ip):
		if ip.count(':'):
			raise OptionError('option %s only IPv4 addresses are currently supported' % name)
		if ip.count('.') != 3:
			raise OptionError('option %s invalid IP address %s' % (name,ip))
		try:
			ipn = 0
			for c in [int(c) for c in ip.split('.')]:
				ipn <<= 8
				ipn += c
		except ValueError:
			raise OptionError('option %s invalid IP address within CIDR %s' % (name,cidr))
		return ip

	def host (self,name,ip):
		self._set(name,self._host(name,self.get(name)))

	def _host (self,name,ip):
		try:
			ip = self.ip(name,ip)
		except OptionError:
			try:
				ip = self.ip(name,socket.gethostbyname(host))
			except socket.gaierror:
				raise OptionError ('option %s could not resolve hostname %s' % (name,host))
		return ip

	def port (self,name):
		self._set(name,self._port(name,self.get(name)))

	def _port (self,name,port):
		return self._number(name,port,low=0,high=2**16-1)

	def netmask (self,name,mask):
		self._set(name,self._netmask(self.get(name)))

	def _netmask (self,name,mask):
		try:
			mask = int(mask)
		except ValueError:
			raise OptionError('option %s the netmask must be an number not %s' % (name,mask))
		if mask < 0 or mask > 32:
			raise OptionError('option %s the netmask is invalid %d' % (name,mask))
		return int(mask)

	def cidr (self,name):
		self._set(name,self._cidr(name,self.get(name)))

	def _cidr (self,name,cidr):
		if not cidr.count('/'):
			cidr+='/32'
		if cidr.count('/') != 1:
			raise OptionError('option %s a cidr is in the form ip/mask' % name)
		ip,mask = cidr.split('/',1)
		
		ip = self._ip("%s ip"%name,ip)
		ipn = toipn(ip)
		mask = self._netmask("%s mask"%name,mask)

		s = pow(2,32-mask)
		if int(ipn/s) * s != ipn:
			raise OptionError('option %s invalid netmask boundary' % name)

		return (ip,mask)

	def service (self,name):
		self._set(name,self._service(name,self.get(name)))

	def _service (self,name,service):
		if service.count(':') != 1:
			raise OptionError('option %s a service is in the form ip:port' % name)
		host,port = service.split(':',1)
		ip = self._ip("%s host"%name,host)
		port = self._port("%s port"%name,port)
		return (ip,port)

	def enum (self,name,values):
		self._set(name,self._enum(name,self.get(name),values))

	def _enum (self,name,value,values):
		if not value in values:
			raise OptionError('option %s value %s is not a valid choice %s' % (name,value,str(values)))
		return value

	def url (self,name):
		self._set(name,self._url(name,self.get(name),values))

	def _url (self,name,url):
		if not url.startswith('http://') and not url.startswith('https://'):
			raise OptionError('option %s url need to starts with http[s]://' % name)
		return url

	def option_debug (self):
		if self.has('debug'):
			self.number('debug',low=0)
		else:
			self._set('debug',0)


if __name__ == '__main__':
	 option = Option().display()
