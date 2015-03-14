# A Modular Approach #

In order to process a high volume of data, ScavengerEXA is built as a modular solution adaptable to many different network topologies.

The complete solution comprises a number of discrete applications, from which users will be able to cherry pick components fulfilling their needs.

The [message flow diagram](http://code.google.com/p/scavengerexa/wiki/message_flow) shows the different parts of ScavengerEXA and how they communicate together.

# Possible Deployment Topology #

ScavengerEXA can be deployed in- or out-of-band to suit the volume of traffic you have and the resources you have available to monitor it

  * An [inline installation topology diagram](http://code.google.com/p/scavengerexa/wiki/topology_inline) shows how low volume networks could deploy scavengerEXA using only one server

  * An [out-of-band installation using mirroring](http://code.google.com/p/scavengerexa/wiki/topology_mirror) demonstrates how we envisage medium networks (under 1GB of monitored traffic) will want to deploy the software

  * An [out-of-band installation using policy routing and mirroring](http://code.google.com/p/scavengerexa/wiki/topology_selective_mirror) demonstrates how we envisage larger networks (multiple GB of traffic) will want to deploy the software

# Overview of each application #

## A capture program ##

[scavenger-capture](http://code.google.com/p/scavengerexa/wiki/scavenger-capture) is designed to gather copies of mails sent by an ISP customer transparently. No mail content is gathered, only the technical conversation including the sender, recipients and if the transactions are successful or not. The captured flows can be sent to one or multiple backends.

## A load dispatching deamon ##

[scavenger-dispatch](http://code.google.com/p/scavengerexa/wiki/scavenger-dispatch) is a network topology aware program whose goal is to take the captured information and dispatch it to one or many daemons which will perform the analysis of the information in order to detect spam patterns, then relay the result to the appropriate ISPs' equipment for action.

## A decision making server ##

[scavenger-policy](http://code.google.com/p/scavengerexa/wiki/scavenger-policy) is a policy application in charge of discovering the infected machines.

Postfix users will be glad to hear that our server can as well be used for normal inbound mail filtering.

The program has been designed to allow the community to contribute extensions in order to improve its efficiency and allows users to select what they know will work best in their networks.

### A way to trap the SPAM ###

[scavenger-mta](http://code.google.com/p/scavengerexa/wiki/scavenger-mta), our dummy mail server can be used to wallgarden a suspected machine until more information can be gathered or the machine infected is cleaned up.

### An Email Notifier ###

[scavenger-action-mail](http://code.google.com/p/scavengerexa/wiki/scavenger-action-mail) is a program sending an email to a nominated postmaster when some spam is detected.

### A wallgarding Program ###

[scavenger-action-netfilter](http://code.google.com/p/scavengerexa/wiki/scavenger-action-netfilter) can be used to automatically configure a linux machine firewall to transparently proxy a detected spammer to a running instance of the dummy MTA.