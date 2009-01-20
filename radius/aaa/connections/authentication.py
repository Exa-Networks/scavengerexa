from zope.interface import implements
from config import IConfigPlugin

from radius.packet.response import RadiusResponse
from radius.packet.functions import encrypt_radius_password, decrypt_radius_password, compare_chap_password

def log(message):
	return
	print message


class IAuthentication(IConfigPlugin):
	def search(request):
		"""	Queries a database of user accounts for the user described in
			the RADIUS authentication request and returns a dictionary that
			describes the configuration of the account
		"""

	def authorise(result, attributes):
		"""	Converts the information that we found on an account and uses it
			to update the attributes that will be returned in the response
		"""

	def authenticate(request, attributes):
		"""	Check that the user is who they say they are or just take their
			word for it
		"""


# XXX: this should become PasswordAuthentication?
class Authentication:
	implements(IAuthentication)

	def __init__(self, name, **args):
		self.name = name
		self.passwordfield = args['password_field']
		self.checkactive = args.get('active', None)
		self.authorisation = args.get('authorisation', [])
		self.initdb(**args)
		
	def search(self, request):
		return {}

	def getPassword(self, result):
		return result.get(self.passwordfield, None)

	def authorise(self, result):
		attributes = {}
		for attribute, values in self.authorisation.items():
			if hasattr(values, '__iter__'):
				values = [v % result for v in values]
			else:
				values = values % result

			if not values:
				continue
			attributes[attribute] = values
		return attributes

	def compareSimple(self, stored_password, request_password):
		return request_password == stored_password

	def _compare(self, request, result):
#		user = request.get('User-Name', None)
#		if user is None:
#			log('no username was supplied with the request')
#			return False
#
		stored_password = self.getPassword(result)
		if stored_password is None:
			log('we found a record for the user but no password')
			return False

		log('stored password is: %s' % stored_password)
		
		if request.has_key('User-Password'):
#			request_password = decrypt_radius_password(request['User-Password'], request.secret, request.authenticator)
			request_password = request['User-Password']
			log('request password is: %s' % request_password)
			authenticated = self.compareSimple(stored_password, request_password)
		else:
			if not request.has_key('CHAP-Password'):
				log('the request came without a password that we know how to read')
				return False

			chap_password = request['CHAP-Password']
			chap_challenge = request.get('CHAP-Challenge', request.authenticator)

			authenticated = compare_chap_password(stored_password, chap_password, chap_challenge)

		if not authenticated:
			log('passwords do not match')
			return False

		return True

	def _checkActive(self, result):
		if self.checkactive is None:
			return True

		for key, value in self.checkactive.iteritems():
			if result.get(key, None) <> value:
				return False

		return True
		

	def authenticate(self, request):
		result = self.search(request)
		active = self._checkActive(result) if result else False
		authenticated = self._compare(request, result) if active else False
		# XXX: clean up attribute copying
		attributes = {}
		attributes.update(request.attributes)
		response = RadiusResponse(request, authenticated, attributes)
		if authenticated:
			response.attributes.update(self.authorise(result))

		if not result:
			response.log('unknown user')
		elif not active:
			response.log('account is not active')
		elif not authenticated:
			response.log('invalid password')

		return response

