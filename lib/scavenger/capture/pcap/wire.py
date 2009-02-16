#!/usr/bin/env python
# encoding: utf-8
"""
wire.py

Created by Thomas Mangin on 2008-12-17.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""
import sys

try:
	import pcap
except ImportError:
	print "this program requires the packet capture library (pcap), dowload it at http://pypi.python.org/pypi/pcap/"
	sys.exit(1)
try:
	import dpkt
except ImportError:
	print "this program requires the dump packet module (dpkt), dowload it at http://pypi.python.org/pypi/dpkt/"
	sys.exit(1)

import time

class Wire (object):
	def __init__ (self,interface=None,promiscuous=False,max=24*60*60):
		self.interface = interface
		self.promiscuous = promiscuous
		self.expire = max
		if max:
			self.expire += time.time()

	def __iter__ (self):
		pc = pcap.pcap(self.interface,promisc=self.promiscuous)
		pc.setfilter('tcp and port 25')
		decode = { pcap.DLT_LOOP:dpkt.loopback.Loopback,
		           pcap.DLT_NULL:dpkt.loopback.Loopback,
		           pcap.DLT_EN10MB:dpkt.ethernet.Ethernet }[pc.datalink()]

		print 'listening on %s: %s' % (pc.name, pc.filter)

		for timestamp, pkt in pc:
			if self.expire and timestamp > self.expire:
				break
			ip = decode(pkt).ip
			tcp = ip.tcp
			sip = 0
			dip = 0
			for c in [ord(c) for c in ip.src]:
				sip <<= 8
				sip += c
			for c in [ord(c) for c in ip.dst]:
				dip <<= 8
				dip += c
			sport = int(tcp.sport)
			dport = int(tcp.dport)
			data = str(tcp.data)
			yield (sip,sport),(dip,dport),data

