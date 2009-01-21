#!/usr/bin/env python
# encoding: utf-8
"""
ld.py

Created by Thomas Mangin on 2008-02-28.
Copyright (c) 2008 Exa Networks Ltd. All rights reserved.
See LICENSE for details.
"""

try:
	import ldap

	class RecipientChecker (object):
		def __init__ (self,configuration):
			self.ldap_server = configuration.get('ldap_server', None)
			self.ldap_port = configuration.get('ldap_port', None)
			self.ldap_user = configuration.get('ldap_user', None)
			self.ldap_password = configuration.get('ldap_password', None)
			self.ldap_dn = configuration.get('ldap_dn', None)
			self.search = configuration.get('ldap_search', '(objectclass=*)')
			self.domains = [d for d in configuration.get('ldap_domains', '').split(' ') if d]

		def exists (self, username, domain):
			if self.domains and not domain in self.domains:
				return False
			
			try:
				l = ldap.initialize('ldap://%s:%s' % (ldap_server, ldap_port))
				l.simple_bind_s(ldap_user, ldap_password)
				dn=ldap_dn % {'username':username,'domain':domain}
				r = l.search_s(dn, ldap.SCOPE_SUBTREE, search)
				if len(r) == 0:
					return False
				return True
			except:
				# could not connect to ldap
				return True

except ImportError:
	from dummy import RecipientChecker

