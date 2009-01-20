from radius.packet.rewriting.regex import RegexRewriteRequest


plugin = RegexRewriteRequest('strip_domain',
	rewrite_field = 'User-Name',
	search = '(.*)@.*',
	replace = '\\1',
)
