#!/usr/bin/env python
# encoding: utf-8
"""
ip.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
"""

import socket
import re

_netmasktoslash = dict()

_netmasktoslash['255.255.255.255'] = 32
_netmasktoslash['255.255.255.254'] = 31
_netmasktoslash['255.255.255.252'] = 30
_netmasktoslash['255.255.255.248'] = 29
_netmasktoslash['255.255.255.240'] = 28
_netmasktoslash['255.255.255.224'] = 27
_netmasktoslash['255.255.255.192'] = 26
_netmasktoslash['255.255.255.128'] = 25

_netmasktoslash['255.255.255.0'] = 24

_netmasktoslash['255.255.254.0'] = 23
_netmasktoslash['255.255.252.0'] = 22
_netmasktoslash['255.255.248.0'] = 21
_netmasktoslash['255.255.240.0'] = 20
_netmasktoslash['255.255.224.0'] = 19
_netmasktoslash['255.255.192.0'] = 18
_netmasktoslash['255.255.128.0'] = 17

_netmasktoslash['255.255.0.0'] = 16

_netmasktoslash['255.254.0.0'] = 15
_netmasktoslash['255.252.0.0'] = 14
_netmasktoslash['255.248.0.0'] = 13
_netmasktoslash['255.240.0.0'] = 12
_netmasktoslash['255.224.0.0'] = 11
_netmasktoslash['255.192.0.0'] = 10
_netmasktoslash['255.128.0.0'] = 9

_netmasktoslash['255.0.0.0'] = 8

_netmasktoslash['254.0.0.0'] = 7
_netmasktoslash['252.0.0.0'] = 6
_netmasktoslash['248.0.0.0'] = 5
_netmasktoslash['240.0.0.0'] = 4
_netmasktoslash['224.0.0.0'] = 3
_netmasktoslash['192.0.0.0'] = 2
_netmasktoslash['128.0.0.0'] = 1

_netmasktoslash['0.0.0.0'] = 0


_sizetoslash = dict()
_slashtosize = dict()

for bits in xrange(1,32+1):
	size = pow(2,32-bits)
	_sizetoslash[size] = bits
	_slashtosize[bits] = size

# return the number of ip contained in a /bits
# input : integer : bits : size of the /
# output : integer : number of ip in that netmask
def tosize(bits):
	return _slashtosize[int(bits)]

# return the netmask in / format for a given number of ip
# input : integer : size : number of ip 
# output : integer : the number of bit for the / of the netmask
def tobits(size):
	return _sizetoslash[int(size)]

def toslash(netmask):
	return _netmasktoslash[netmask]

ipchecker = re.compile('^(\d{3}\.){1,3}\d{1,3}$')
def isip(value):
	if ipchecker.match(value):
		return True
	return False

def toips (ipn):
	d = str(ipn & 255)
	c = str((ipn >> 8) & 255)
	b = str((ipn >> 16) & 255)
	a = str((ipn >> 24) & 255)
	return '.'.join([a,b,c,d])

def toipn (ips):
	a,b,c,d = ips.split('.')
	return (int(a) << 24) + (int(b) << 16) + (int(c) << 8) + int(d)

def tostartend (cidr):
	if not cidr.count('/'):
		cidr+='/32'
	ip,mask = cidr.split('/')

	if ip.count(':'):
		raise ValueError('only IPv4 is currently supported')

	if ip.count('.') != 3:
		raise ValueError('invalid IP address within CIDR %s' % cidr)

	try:
		start = 0
		for c in [int(c) for c in ip.split('.')]:
			start <<= 8
			start += c
	except ValueError:
		raise ValueError('invalid IP address within CIDR %s' % cidr)
	try:
		mask = int(mask)
	except ValueError:
		raise ValueError('the netmask must be an integer not %s' % mask)

	if mask < 0 or mask > 32:
		raise ValueError('the netmask is invalid %d' % mask)

	s = pow(2,32-mask)

	if int(start/s) * s != start:
		raise ValueError('invalid netmask boundary')

	end = start + s - 1
	return start,end


_next = {} 

def next_server (servers):
	while True:
		for server in servers:
			yield server

def send_udp (diffusion,address,servers,message):
	p = str(message)
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

	tmp = servers[:]
	tmp.sort()
	key = str(tmp)

	if diffusion == 'one':
		server = servers[0]
		sock.sendto(p,server)
	elif diffusion == 'rr':
		if key not in _next:
			_next[key] = next_server(servers)
		server = _next[key].next()
		sock.sendto(p,server)
	elif diffusion == 'sr':
		hash = int(address.split('.')[-1]) % len(servers)
		server = servers[hash]
		sock.sendto(p,server)
	elif diffusion == 'all':
		for server in servers:
			sock.sendto(p,server)
	else:
		raise ValueError('invalid value for diffusion : %s', str(diffusion))
