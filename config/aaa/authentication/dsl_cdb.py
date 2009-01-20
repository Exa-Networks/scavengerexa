from radius.aaa.authentication.authcdb import CDBAuthentication

plugin = CDBAuthentication('dsl_cdb',
	cdbfile = '/home/david/test/newusers.cdb',
	format = ('userPassword', 'radiusFramedIPAddress', 'ipRoute', 'policy', 'active'),
	active = {'active':'active'},
	delimiter = '\0',
	password_field = 'userPassword',
	authorisation = {
		'Cisco-AVPair:ip:route' : '%(ipRoute)s',
		'Cisco-AVPair:ip:dns-servers' : '82.219.4.24 82.219.4.25',
		'Cisco-AVPair:sub-qos-policy-out' : '%(policy)s',
		'Framed-IP-Address' : '%(radiusFramedIPAddress)s',
		'Framed-IP-Netmask' : '255.255.255.255',
		'Service-Type' : 'Framed-User',
		'Framed-Protocol' : 'PPP'
	},
	search_key = '%(User-Name)s'
)
