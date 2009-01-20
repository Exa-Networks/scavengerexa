from zope.interface import implements
from config import IConfigPlugin


class IAuthorisation(IConfigPlugin):
	def search(request):
		"""	Queries a database of user accounts for the user described in
			the RADIUS authentication request and returns a dictionary that
			describes the configuration of the account
		"""

	def authorise(result, attributes):
		"""	Converts the information that we found on an account and uses it
			to update the attributes that will be returned in the response
		"""


class Authorisation:
	implements(IAuthorisation)

	def __init__(self, name, **args):
		self.name = name
		self.authorisation = args.get('authorisation', [])
		self.filter = args.get('filter', None)
		self.match = args.get('match', None)
		self.initdb(**args)

	def initdb(self, **args):
		pass
		
	def search(self, request):
		return {}

	def _authorise(self, result):
		attributes = {}
		for attribute, field in self.authorisation.items():
			value = result.get(field, None)
			if not value:
				continue
			attributes[attribute] = value
		return attributes

	def _isFiltered(self, request):
		if self.filter is None:
			return False

		for key, values in self.filter.iteritems():
			if request.get(key, None) in values:
				return True
		return False

	def _isMatched(self, request):
		if self.match is None:
			return True

		for key, values in self.match:
			if request.get(key, None) not in values:
				return False

		return True

	def authorise(self, request, response):
		if self._isFiltered(request):
			return {}

		if not self._isMatched(request):
			return {}

		result = self.search(request)
		return dict(((key, value) for key, value in result.iteritems() if key not in response))
