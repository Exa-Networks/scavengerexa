from __future__ import with_statement
from radius.aaa.connections.authentication import Authentication

class StaticAuthentication(Authentication):
	def initdb(self, **args):
		self.response = args['response']

	def _compare(self, request, result):
		return self.response

	def search(self, request):
		# XXX: we need a non-db oriented Authentication module so we don;t have to do this
		return True
