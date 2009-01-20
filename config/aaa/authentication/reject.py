from radius.aaa.authentication.static import StaticAuthentication

plugin = StaticAuthentication('reject',
	password_field = None,
	response = False,
)
