# Topology Inline #

This diagram demonstrates how ScavengerEXA can be used inline (for small/medium networks) to automate the blocking of infected hosts.

In this scenario, mail conversations (and mail conversations only) are policy routed to a linux server configured to act like a router.
The Linux machine has two routes:
  * a default route to the Internet (right on the diagram)
  * a more specific route for the user it protects (to route DSL traffic back where it should go)

the 'action-netfilter' application can then be used to filter infected hosts, performing a PREROUTING of the packet and de-NATing intercepted spam to a locally run 'dummy MTA' (an MTA always reporting 450 errors on DATA).

<img src='http://scavengerexa.googlecode.com/hg/documentation/image/diagram-topology1.png' alt='diagram-topology1.png' width='700' title='diagram-topology1.png' />