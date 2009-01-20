from radius.aaa.authorisation.dynamic import LambdaAuthorisation

plugin = LambdaAuthorisation('nasportip',
	authorisation = {
		'Framed-IP-Address' : lambda request: '127.0.0.' + str(request['NAS-Port']),
		'Framed-IP-Netmask' : lambda request: '255.255.255.255'
	},
)
