from struct import pack
from socket import htonl

from zope.interface import implements
from twisted.plugin import IPlugin

from radius.config.handler import Handler


plugin = Handler('dsl',
	type = 'AUTH_UNTIL_ANSWER',
	match = {
		'User-Name' : ".*@dsl.domain$"
	},

	# pre_auth, auth, post_auth and acct all default to None
	# they will be defined as a string or a list of strings
	mangle = 'adsl_to_dsl',
	auth = 'dsl_cdb',
	acct = 'dsl_mysql',
	authorise = 'policy_speed'
)
