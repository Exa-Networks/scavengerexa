from radius.packet.rewriting.regex import RegexRewriteRequest


plugin = RegexRewriteRequest('adsl_to_dsl',
	rewrite_field = 'User-Name',
	search = '(.*)@adsl.(.*)',
	replace = '\\1@dsl.\\2',
)
