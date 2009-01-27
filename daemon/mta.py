#!/usr/bin/env python
# encoding: utf-8
"""
mta.py

Created by Thomas Mangin on 2007-04-01.
Copyright (c) 2008 Exa Networks. All rights reserved.
See LICENSE for details.
"""

from __future__ import with_statement

import sys

# Enabling (or not) psycho

try:
	import psyco
	psyco.full()
	print 'Psyco found and enabled'
except ImportError:
	print 'Psyco is not available'

# Options

from scavenger.option import Option as BaseOption, OptionError

class Option (BaseOption):
	valid = ['debug','port','smarthost','hostname','organisation','domains','roles','contact','limit','timeout','control','url']

	def option_port (self):
		self.port('port')
		
	def option_smarthost (self):
		if self.has('smarthost'):
			self.set('smarthost')
		else:
			self._set('smarthost','127.0.0.1')

	def option_hostname (self):
		if self.has('hostname'):
			self.set('hostname')
		else:
			self._set('hostname','locahost.localdomain')

	def option_organisation (self):
		self.set('organisation')

	def option_domains (self):
		if self.has('domains'):
			self.list('domains')
		else:
			self._set('domains',[self['hostname'],])

	def option_roles (self):
		if self.has('roles'):
			self.list('roles')
		else:
			self._set('roles',['postmaster','abuse'])

	def option_contact (self):
		if self.has('contact'):
			self.set('contact')
		else:
			if self.has('domain'):
				self._set('contact',self.get('contact'))
			elif self.has('hostname'):
				self._set('contact',self.get('hostname'))
			else:
				self._set('contact','postmaster@%s'%socket.gethostname())

	def option_limit (self):
		if self.has('limit'):
			self.number('limit',low=1)
		else:
			self._set('limit',50)

	def option_timeout (self):
		if self.has('timeout'):
			self.number('timeout',low=0)
		else:
			self._set('timeout',20)

	def option_control (self):
		if self.has('control'):
			self.set('control')
		else:
			self._set('control','control')

	def option_url (self):
		self.url('url')

try:
        option = Option().option
except OptionError, e:
        print str(e)
        sys.exit(1)

# Debugging

debug_option = not not option.debug & 1
debug_connection = not not option.debug & 2
debug_conversation = not not option.debug & 4

if debug_option:
	option.display()
	print 'debug connection  ',debug_connection
	print 'debug conversation',debug_conversation
	print "+"*80

# Variables ....

forget='forget'
stat='stat'

message = {
	'greeting':      "220 %s ESMTP [%s] [connection %s/%d seen %s]" % (option.hostname,option.organisation,'%d',option.limit,'%s'),
	'overloaded':    "421 %s ESMTP [%s] [max connection %d reached seen %s, connection refused]" % (option.hostname,option.organisation,option.limit,'%d'),
	'helo':          "250 %s [%s]" % (option.hostname,option.organisation),
	'ehlo':          "250-%s [%s]\r\n"
	                 "250-your ability to send mail has been restricted\r\n"
	                 "250-please visit %s\r\n"
	                 "250 or contact %s"
	                  % (option.hostname,option.organisation,option.url,option.contact),
	'help':          "214-restricted mail transport agent\r\n"
	                 "214-this mta can only send mail to the following users\r\n"
	                 "214-%s\r\n"
	                 "214-and the following domains\r\n"
	                 "214-%s\r\n"
	                 "214-for more information visit %s\r\n"
	                 "214 and contact %s"
	                  % (option.url, "@, ".join(option.roles)+"@", ", ".join(option.domains), option.contact),
	'lazy':          "502 unimplemented",
	'timeout':       "421 connection timeout",
	'mail_first':    "503 MAIL first",
	'rcpt_first':    "503 RCPT first",
	'email_denied':  "554 invalid email address",
	'ok':            "250 ok",
	'ready':         "250 ready",
	'queued':        "250 ok mail queued",
	'not_queued':    "451 could not send this mail, please retry later",
}


info = {
	'help':         "214-this is the mta information mode\r\n"
	                "214-%-10s : show how many connection the deamon got from clients\r\n"
	                "214-%-10s : reset all the counters\r\n"
	                "214 ready when you are"
	                 % (stat,forget),
	stat:           "214-\r\n214 now go and crucify the infidel",
	forget:         "250 what did i do ?",
}

answer = {
	'pass' : {
		'rcpt' : "250 ok",
		'data' : "354 listening, come on ...",
		'quit' : "250 bye bye",
		},
	'block' : {
		'rcpt' : "450 only mail to %s and the administrative domain are allowed" % ", ".join(option.roles),
		'data' : "451 this mail will not be sent, please contact %s" % option.contact,
		'quit' : "221 no mail was sent, please contact %s, bye" % option.contact,
	},
}


# Imports

import sys
import time
import socket
import smtplib
import threading

# Global functions


def log (message):
	print >> sys.stderr, message
	sys.stderr.flush()

def log_connection (message):
	if debug_connection:
		log(message)

def log_conversation (message):
	if debug_conversation:
		log(message)

# MAIN

from twisted.application import internet, service
from twisted.internet import protocol, reactor
from twisted.protocols import basic
from twisted.protocols import policies

class MailProtocol(basic.LineReceiver):
	def connectionMade(self):
		self.info = False
		self.state = 'block'
		self.sender = ""
		self.recipient = []
		self.ehlo = ""
		self.content = ""
		self.length = 0
		self.in_data = False
		self.seen = 0
		self.accepted = False
		
		self.seen,index = self.factory.connect(self.transport)
		
		self.ip = self.transport.getPeer().host
		try:
			self.host = socket.gethostbyaddr(self.ip)[0]
		except:
			self.host = 'unknown'
		
		if index != 0:
			self.accepted = True
			self.to_client(message['greeting'] % (index,self.seen))
		else:
			self.accepted = False
			self.to_client(message['overloaded'] % self.seen)
			self.transport.loseConnection()

	def connectionLost(self, reason):
		log_connection("connection %d closing" % self.seen)
		self.factory.disconnect(self)
	
	def dataReceived (self,data):
		try:
			self.process(data)
		except Exception, e:
			log('Problem with the server : '+ str(e))
			self.transport.loseConnection()
			return
	
	def extract (self,line):
		line = line.strip()
		try:
			# mail from: <destination>
			# mail from: destination-from-rfc821-ignorant
			
			end = '>'
			p = line.split('<')
			if len(p) != 2:
				end = ' '
				p = line.split(':')
				if len(p) != 2:
					return None
			destination = p[1].strip()
			
			# if destination as "@ONE,@TWO:JOE@THREE" (see RFC 821) then strip the routing to only keep JOE@THREE
			
			if destination[0] == '@':
				p = destination.split(':')
				if len(p) != 2:
					raise
				destination = p[1]
				
			escaped = True
			quoted = False
			email = ""
			
			for c in destination:
				if escaped:
					email += c
					escaped = False
				else:
					if not quoted and c == end:
						break
					if c == '\\':
						escaped = True
					elif c == '"':
						quoted = not quoted
					else:
						email += c
						
			# The email is invalid
			if quoted or escaped:
				return None
				
			if email.count('@') != 1:
				return None
				
			return email
			
		except:
			return None

	def sendmail (self):
		try:
			smtp = smtplib.SMTP(option.smarthost,25,option.hostname)
			#smtp.set_debuglevel(1)
			smtp.sendmail(self.sender,self.recipient,self.content)
			smtp.close()
			return True
		except Exception, e:
			return False

	def to_client (self,message):
		try:
			self.transport.write(message + '\r\n')
		except:
			# the client killed the connection without sending 
			self.transport.loseConnection()

	def process (self,line):
		if self.in_data:
			self.process_data(line)
		else:
			self.process_command(line)

	def process_data (self,line):
		if line.strip() != ".":
			self.content += line
			self.length += len(line)
			
			if self.length > 100000:
				raise ValueError("as you need")
		else:
			self.in_data = False
			
			if self.sendmail():
				log('connection %d mail sent from %s to %s' % (self.seen,self.sender,str(self.recipient)))
				self.to_client(message['queued'])
			else:
				log('connection %d mail denied from %s to %s' % (self.seen,self.sender,str(self.recipient)))
				self.to_client(message['not_queued'])
		
	def process_command (self,line):
		parts = line.lower().split(' ')
		if not len(parts):
			self.to_client(message['lazy'])
			return

		cmd = parts[0].lower().strip()

		if cmd == 'quit':
			self.to_client(answer[self.state][cmd])
			self.transport.loseConnection()
			return

		elif cmd == 'mail':
			self.sender = ""
			email = self.extract(line)
			if email == None:
				log_conversation('connection %d denied sender %s' % (self.seen,line.strip()))
				self.to_client(message['email_denied'])
				return

			log_conversation('connection %d sender is %s' % (self.seen,email))
			self.sender = email
			self.to_client(message['ok'])
			
		elif cmd == 'rcpt':
			local = 'block'
			if self.sender == "":
				self.to_client(message['mail_first'])
				log_conversation('connection %d forgot to give us a sender' % self.seen)
				return

			email = self.extract(line)
			log_conversation('connection %d recipient is %s' % (self.seen,email))
			if email == None:
				self.to_client(message['email_denied'])
				return

			for role in option.roles:
				if email.startswith(role+'@'):
					self.state = 'pass'
					local = 'pass'

			for domain in option.domains:
				if email.endswith("@"+domain):
					self.state = 'pass'
					local = 'pass'

			if local == 'pass':
				self.recipient.append(email)
				log_conversation('connection %d allowed recipient %s' % (self.seen,email))
			else:
				log_conversation('connection %d denied recipient %s' % (self.seen,email))

			self.to_client(answer[local][cmd])
			return

		elif cmd == 'data':
			if self.sender == "":
				self.to_client(message['mail_first'])
				return

			if self.recipient == []:
				self.to_client(message['rcpt_first'])
				return

			self.to_client(answer[self.state][cmd])
			if self.state == 'block':
				return

			self.in_data = True

			if self.ehlo != "":
				self.ehlo = "(HELO %s) " % self.ehlo
			if self.ip != "unknown":
				self.ip = "([%s])" % self.ip

			self.content = """"Received: from %s %s%s
          (envelope-sender <%s>)
          by %s (mta-spam) with SMTP
          for <%s>; %s -0000\r\n""" \
			% (self.host,self.ehlo,self.ip,self.sender,option.hostname,self.recipient[0],time.strftime("%d %b %Y %H:%M:%S",time.gmtime()))

			return

		elif cmd in ('helo','ehlo'):
			log_conversation('connection %d client is saying : %s' % (self.seen,line.strip()))
			if len(parts) > 1:
				self.ehlo = parts[1].strip()
			self.to_client(message[cmd])
			return

		elif cmd == 'help':
			log_conversation('connection %d asked for help' % self.seen)
			if self.info:
				self.to_client(info['help'])
			else:
				self.to_client(message['help'])
			return

		elif cmd == 'rset':
			log_conversation('connection %d asked for a reset' % self.seen)
			self.sender = ""
			self.recipient = []
			self.to_client(message['ready'])
			return

		elif cmd == 'noop':
			log_conversation('connection %d asked for a noop' % self.seen)
			self.to_client(message['ok'])
			return

		elif cmd == 'exit':
			log_conversation('connection %d leaving' % self.seen)
			self.to_client(answer[self.state]['quit'])
			self.transport.loseConnection()
			return

		elif cmd == option.control:
			self.info = not self.info
			self.to_client(message['ok'])
			return

		elif cmd == stat:
			if self.info:
				for ip,f,l,c,r,s in self.factory.status():
					self.to_client("214- %-12s  %-12s  %-16s %3s connected, %4s refused, %8s seen" % (f,l,ip,c,r,s))
				self.to_client(info['stat'])
			else:
				self.to_client(message['lazy'])
			return

		elif cmd == forget:
			if self.info:
				if len(parts) > 1: ip = parts[1].strip()
				else: ip = None
				self.factory.forget(ip)
				self.to_client(info[forget])
			else:
				self.to_client(message['lazy'])
			return

		#elif cmd in ('vrfy','expn'):
		else:
			self.to_client(message['lazy'])
			return

class MailFactory(protocol.ServerFactory):
	protocol = MailProtocol
	
	def __init__ (self):
		self.lock = threading.Lock()
		self.connected = {}
		self.refused = {}
		self.seen = {}
		self.first = {}
		self.last = {}
	
	def connect (self,transport):
		ip = transport.getPeer().host
		with self.lock:
			if not self.first.has_key(ip):
				self.first[ip] = time.strftime("%d %b %H:%M",time.localtime())
			self.last[ip] = time.strftime("%d %b %H:%M",time.localtime())
			
			seen = self.seen.get(ip,0) + 1
			self.seen[ip] = seen
			
			connected = self.connected.get(ip,0)
			
			if connected < option.limit:
				connected += 1
				self.connected[ip] = connected
				self.refused[ip] = 0
				log_connection('connection %d from %s accepted connection %d/%d' % (seen,ip,connected,option.limit))
				return seen,connected
			
			self.connected[ip] = connected
			self.refused[ip] += 1
		
		transport.loseConnection()
		log_connection('%s connection %d, refused %d' % (ip,seen,self.refused[ip]))
		return seen,0

	def disconnect (self,protocol):
		ip = protocol.transport.getPeer().host
		if protocol.accepted:
			with self.lock:
				self.connected[ip] -= 1
				if self.connected[ip] == 0:
					del self.connected[ip]
		protocol.transport.loseConnection()
	
	def status (self):
		rs = []
		
		with self.lock:
			for ip in self.seen.keys():
				first = str(self.first.get(ip,'N/A'))
				last = str(self.last.get(ip,'N/A'))
				seen = str(self.seen.get(ip,'None'))
				connected = str(self.connected.get(ip,0))
				refused = str(self.refused.get(ip,'None'))
				
				rs.append((ip, first, last, connected, refused, seen))
		
		for r in rs:
			yield r
	
	def forget (self,ip):
		with self.lock:
			if self.seen.has_key(ip):
				log("removed statistic for %s" %ip)
				del self.refused[ip]
				del self.seen[ip]
				del self.first[ip]
				del self.last[ip]
			
			if ip == None:
				log("removing statistic all ips")
				self.refused = {}
				self.seen = {}
				self.first = {}
				self.last = {}
	
	
application = service.Application('mta-spam')
serviceCollection = service.IServiceCollection(application)

factory = policies.TimeoutFactory(MailFactory(),timeoutPeriod=option.timeout)
internet.TCPServer(option.port, factory).setServiceParent(serviceCollection)

serviceCollection.startService()
reactor.run()
sys.exit(1)

