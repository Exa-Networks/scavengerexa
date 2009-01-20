from __future__ import with_statement
from radius.aaa.connections.authentication import Authentication


import ldap
class simpleldap:
	def __init__(self, server, port, user, password, filter=None, scope=None, base=None):
		self.server = server
		self.port = port
		self.user = user
		self.password = password
		self.filter = filter if filter is not None else '(objectclass=*)'
		self.scope = scope if scope is not None else ldap.SCOPE_SUBTREE
		self.base = base
		self.connection = None
		self.__connect()

	def __connect(self):
		self.connection = ldap.initialize('ldap://%s:%s' % (self.server, self.port))
		try:
			self.connection.simple_bind_s(self.user, self.password)
		except ldap.SERVER_DOWN:
			raise 


	def search(self, base=None, scope=None, filter=None, fields=None):
		if base is None:
			if self.base is None:
				raise QUERYERROR, 'no base specified to filter from'
			base = self.base

		filter = filter if filter is not None else self.filter
		scope = scope if scope is not None else self.scope
		
		try:
			res = self.connection.search_s(base, scope, filter, fields)
		except ldap.SERVER_DOWN:
			self.__connect()
			res = self.connection.search_s(base, scope, filter, fields)

		return res
			


class LDAPAuthentication(Authentication):
	def initdb(self, **args):
		self.requestfields = [self.passwordfield] + self.authorisation.values()
		self.search_string = args['search_string']
		self.base = args['base']
		self.scope = args.get('scope', ldap.SCOPE_SUBTREE)

		server = args['server']
		port = args['port']
		user = args['user']
		password = args['password']
		self.connection = simpleldap(server, port, user, password)

	def search(self, request):
		result = self.connection.search(self.base, self.scope, self.search_string % request, self.requestfields)
		if result:
			try:
				key, value = result[0]
				for k, v in value.iteritems():
					value[k] = v[0]
				return value
			except TypeError:
				return None
		return result

