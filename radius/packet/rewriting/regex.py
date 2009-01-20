from zope.interface import implements
from config import IConfigPlugin

import re


class IRequestRewrite(IConfigPlugin):
	def __call__(request):
		"""Rewrite and/or add/delete attributes in a RADIUS request"""

class RegexRewriteRequest:
	implements(IRequestRewrite)

	def __init__(self, name, **args):
		self.name = name
		self.rewrite_field = args.get('rewrite_field', None)
		self.search = args.get('search', '')
		self.replace = args.get('replace', '')
		self.re = re.compile(self.search)

	def __call__(self, request):
		if self.re is None:
			return None

		if request.has_key(self.rewrite_field):
			request[self.rewrite_field] = self.re.sub(self.replace, request[self.rewrite_field])
		return request
