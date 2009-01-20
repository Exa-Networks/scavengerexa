from zope.interface import implements
from config import IConfigPlugin


class IAccounting(IConfigPlugin):
	def initdb(**args):
		""" Module specific initialisation
		"""

	def log(request, response):
		"""	Create a record of who authenticated and what our response was
		"""

class Accounting:
	implements(IAccounting)

	def __init__(self, name, **args):
		self.name = name
		self.initdb(**args)

	def initdb(self, **args):
		pass

	def log(self, request, response):
		pass
		
