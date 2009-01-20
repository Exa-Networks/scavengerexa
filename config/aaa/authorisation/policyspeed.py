from radius.aaa.authorisation.static import StaticAuthorisation

plugin = StaticAuthorisation('policy_speed',
	filter = {
		'User-Name' : ('thomas.mangin@dsl.exa-networks.co.uk', 'mark.cowgill@dsl.exa-networks.co.uk')
	},
	authorisation = {
		'Cisco-AVPair:sub-qos-policy-out' : 'dsl-10G',
	},
)
