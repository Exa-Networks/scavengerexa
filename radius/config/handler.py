from zope.interface import implements
from config import IHandlerConfig, ConfigError

import re
from radius.packet.response import RadiusResponse

class Handler:
	implements(IHandlerConfig)

	def __init__(self, name, **args):
		self.name = name
		self.type = args.get('type', 'AUTH_UNTIL_ANSWER')
		self.match = args.get('match', {})
		self.conditions = args.get('conditions', {})
		
		self.mangle = args.get('mangle', None)
		self.auth = args.get('auth', None)
		self.acct = args.get('acct', None)
		self.authorise = args.get('authorise', None)

		self.pool = args.get('pool', None)


	def matches(self, pkt):
		for key, value in self.match.iteritems():
			if not pkt.has_key(key):
				return False
			if hasattr(pkt[key], '__iter__'):
				if True not in [value.match(pkt_value) is not None for pkt_value in pkt[key]]:
					return False
			else:
				if not value.match(pkt[key]):
					return False
		return True

	def rewriteRequest(self, request):
		for mangle in self.mangle:
			print mangle
			rewritten = mangle(request)
			if rewritten is None:
				continue
			request = mangle(request)
		return request

	# XXX: currently hardcoded as auth_until_result
	def authenticate(self, pkt):
		for authenticator in self.auth:
			res = authenticator.authenticate(pkt)
			if res is not None:
				return res

		# XXX: hardcoded as fail closed
		return RadiusResponse(False)

	def account(self, pkt):
		for accountant in self.acct:
			res = accountant.log(pkt)
			if res is not None:
				return res

	def postauth(self, pkt, attrs):
		for authoriser in self.authorise:
			attrs = authoriser.authorise(pkt, attrs)
		return attrs

	def assign(self, pkt, attrs):
		res = None
		for pool in self.pool:
			res = self.pool.assign(pkt, attrs)
			if res is not None:
				break

		if res is not None:
			attrs.update(res)

		return attrs

	def deassign(self, pkt):
		if self.pool is not None:
			self.pool.deassign(pkt)


	def InitialiseMatch(self):
		for key, value in self.match.items():
			self.match[key] = re.compile(value)


	def InitialisePart(self, string_values, functions):
		if not string_values:
			return []

		if not hasattr(string_values, '__iter__'):
			string_values = [string_values]

		function_list = []
		for name in string_values:
			function = functions.get(name, None)
			if function is None:
				raise ConfigError, 'hander %s wants to use undefined function %s' % (self.name, name)
			function_list.append(function)

		return function_list

	def initialise(self, config):
		self.auth = self.InitialisePart(self.auth, config.getAuthenticators())
		self.acct = self.InitialisePart(self.acct, config.getAccountants())
		self.mangle = self.InitialisePart(self.mangle, config.getManglers())
		self.authorise = self.InitialisePart(self.authorise, config.getAuthorisers())
		self.pool = self.InitialisePart(self.pool, config.getPools())
		
		self.InitialiseMatch()
		return self


