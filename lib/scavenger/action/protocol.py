#!/usr/bin/env python
# encoding: utf-8
"""
server.py

Created by Thomas Mangin on 2009-01-10.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import re

match_hold = re.compile("\((\d+)\)\s+(.*)")
match_filter = re.compile("\[([\d.]+):(\d+)\] \((\d+)\)\s+(.*)")

from twisted.protocols.basic import LineReceiver

class ActionProtocol (LineReceiver):
	debug = False

	def invalid (self):
		self.transport.write('INVALID\r\n')
		self.transport.loseConnection()

	def valid (self):
		self.transport.write('OK\r\n')
		self.transport.loseConnection()

	def dataReceived (self,data):
		try:
			action,ip,message = data.strip().split(' ',2)
		except (ValueError,TypeError):
			self.invalid()
			return

		duration = 0
		destination = ''

		if action == 'DUNNO':
			pass
		elif action == 'HOLD':
			r = match_hold.search(message)
			if r:
				duration = int(r.group(1))
				message = r.group(2)
			else:
				self.invalid()
				return
		elif action == 'FILTER':
			r = match_filter.search(message)
			if r:
				destination = r.group(1) + ':' + r.group(2)
				duration = int(r.group(3))
				message = r.group(4)
			else:
				self.invalid()
				duration = 0

		# check the destination IP

		self.valid()
		print 'ip=%-15s act=%-7s dest=%-21s dur=%-5s msg="%s"' % (ip,action,destination,duration,message)
		self.run(ip,action,destination,duration,message)

