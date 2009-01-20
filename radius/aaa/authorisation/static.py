from __future__ import with_statement
from radius.aaa.connections.authorisation import Authorisation


class StaticAuthorisation(Authorisation):
	def search(self, request):
		return self.authorisation
