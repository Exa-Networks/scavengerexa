from radius.config.handler import Handler


plugin = Handler('dialup',
	match = {
		'User-Name' : ".*@dialup.domain$",
		'NAS-IP-Address' : '127.0.0.2',
	},

#	mangle = 'strip_domain',
	auth = 'dialup_cdb',
	authorise = 'nasportip'
)
