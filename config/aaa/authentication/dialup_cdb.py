from radius.aaa.authentication.authcdb import CDBAuthentication

plugin = CDBAuthentication('dialup_cdb',
	cdbfile = '/home/david/test/dialup.cdb',
	format = ('userPassword', 'radiusFramedIPAddress', 'active'),
	active = {'active':'active'},
	delimiter = '\0',
	password_field = 'userPassword',
	authorisation = {
		'Cisco-AVPair:ip:dns-servers' : '82.219.4.24 82.219.4.25',
		'Framed-IP-Address' : '%(radiusFramedIPAddress)s',
#		'Framed-IP-Netmask' : '255.255.255.255',
		'Session-Timeout' : '86400',
		'Idle-Timeout' : '3600',

	},
	search_key = '%(User-Name)s'
)
