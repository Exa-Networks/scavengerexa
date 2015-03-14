# Partial Out of band topology #

In this scenario, a network administrator will first separate mail flows from other traffic and then use network equipment to mirror the mail traffic only to a capture server, which will then send its captured message via the network to some possibly shared dispatch and policy servers.

The DSL user will then be blocked using some other means like an email to the NOC to block the machine, or scavenger-action-radius which will change the customer profile and force a re-authentication.

<img src='http://scavengerexa.googlecode.com/hg/documentation/image/diagram-topology3.png' alt='diagram-topology3.png' width='700' title='diagram-topology3.png' />