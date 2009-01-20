from __future__ import with_statement
from radius.aaa.connections.authorisation import Authorisation


class LambdaAuthorisation(Authorisation):
	def search(self, request):
		return dict(((k,v) for k,v in ((key, l(request)) for key, l in self.authorisation.iteritems()) if v is not None))
