#!/usr/bin/env python
# encoding: utf-8
"""
vm.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

try:
	#from exa.djb.qmail.vmailmgr.client import Client as vmailClient, VmailError
	from vdomain.client import Client as vmailClient, VmailError

	class RecipientChecker (object):
		def __init__ (self,configuration):
			self.host = configuration.get('vmail_host')
			self.port = configuration.get('vmail_port')
			self.password = configuration.get('vmail_password')
			self.domains = [d for d in configuration.get('vmail_domains', '').split(' ') if d]

		def exists (self, username, domain):
			if self.domains and not domain in self.domains:
				return False
			
			for user in username, '+':
				try:
					vmail = vmailClient(self.host, self.port, domain, '***')
					vmail.lookup(user.lower(),'an-invalid-password')
					# The improbabable case where the password was right !
					return True
				except VmailError.InvalidDomain:
					# the domain is not a vmailmgr domain (must be a domain we relay for)
					return True
				except VmailError.BackendUnknown:
					# Assuming that the domain will not have gotten here if we do not host it
					return True
				except VmailError.BackendUnavailable:
					# The backend server is known but went down, fail open
					return True
				except VmailError.ConnectionError:
					# we couldn't connect to the proxy, fail open
					return True
				except VmailError.InvalidUser:
					# No user, need to check the catchall
					pass
				except VmailError.InvalidPassword:
					# The user exists and we gave the wrong password
					return True
				except VmailError.Unimplemented:
					# The vmail server doesn't know about the method we tried to call, fail open
					return True
				except:
					# warning: triggered change in the vmailmgr api checking catchall for the domain failing open
					# warning: or we have another bug this is hidding (but we MUST not bounce)
					return True

			try:
				vmail = vmailClient(self.host, self.port, domain, self.password)
				if vmail.getoption('', 'catchall'):
					return True
			except Exception, e: # XXX: this is bad. we should not be hiding the error like this
				print str(type(e)), str(e)
				return True

			return False

except ImportError:
	from dummy import RecipientChecker
