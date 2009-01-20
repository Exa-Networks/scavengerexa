#!/usr/bin/env python

import sys

from twisted.internet import protocol, reactor, defer
from twisted.application import internet, service
from twisted.python import components

from config import GlobalConfig

from radius.server.factory import RadiusAuthServerFactory
from radius.server.factory import RadiusAcctServerFactory
from radius.server.service import RadiusService

for config in GlobalConfig():
	auth_ip, auth_port = config.getAuthAddr()
	acct_ip, acct_port = config.getAcctAddr()

	s = RadiusService('/opt/scavenger/db/action_radius')

	if auth_ip is not None:
		auth_factory = RadiusAuthServerFactory(config, s, reactor.callInThread)
		reactor.listenUDP(auth_port, auth_factory.buildProtocol())


	#if acct_ip is not None:
	#	acct_factory = RadiusAcctServerFactory(config, s)
	#	reactor.listenUDP(acct_port, acct_factory.buildProtocol())

# Starting ...

from twisted.application import internet, service
from twisted.protocols import policies

application = service.Application('action-radius')
serviceCollection = service.IServiceCollection(application)

reactor.suggestThreadPoolSize(50)

serviceCollection.startService()
reactor.run()
sys.exit(1)

