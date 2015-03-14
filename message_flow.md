## Message Flow ##

Here is how the information flows between the different applications constituing ScavengerEXA.

This flow illustrates how the capture application can pass the information gathered to multiple dispatch backends, using source hashing on the address of the mail sender or round robin.

The dispatch server will then query a policy daemon (always the same for a given sender) and will then pass the answer, if the message was tagged as spam, to the the appropriate action server.

The dispatch server can have multiple action servers configured, each action server looking after different range of IP addresses which incoming mail can be sent from.

Each action-server is in charge of a unique range of IP addresses, and the dispatch server will send the request to the appropriate one.

If more than one action server is defined for a range, then the message will be sent more than once, allowing multiple actions (like sending an email AND blocking the sender).

The action-mail software is the simplest example of an action program. It will email the spammer's IP address to the network's postmaster for action.

In a 'low load' environment, all those programs could of course run on a single machine.

<img src='http://scavengerexa.googlecode.com/hg/documentation/image/diagram-message-flow.png' alt='diagram-message-flow.png' width='700' title='diagram-message-flow.png' />