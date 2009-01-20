from radius.aaa.accounting.acctmysql import MySQLAccounting

plugin = MySQLAccounting('dsl_mysql',
	server	= '',
	db	= 'accounting',
	user	= 'david',
	password	= '',
	insert_table	= 'acct_dsl',
	fields	=	{
		'username' : '%(User-Name)s',
		'ip_addr' : '%(Framed-IP-Address)s',
		'ip_route' : '%(Cisco-AVPair:ip:route)s',
		'speed' : '%(Connect-Info)s',
		'policy' : '%(Cisco-AVPair:sub-qos-policy-out)s',

		'type' : '%(Acct-Status-Type)s',
		'session_id' : '%(Acct-Session-Id)s',
		'session_time' : '%(Acct-Session-Time)s',
		'delay' : '%(Acct-Delay-Time)s',
		'term_cause' : '%(Acct-Terminate-Cause)s',

		'nas_id' : '%(NAS-Identifier)s',
		'nas_ip' : '%(NAS-IP-Address)s',
		'nas_port' : '%(NAS-Port)s',
		'caller_id' : '%(Calling-Station-ID)s',
		'called_id' : '%(Called-Station-ID)s',

	}
)

