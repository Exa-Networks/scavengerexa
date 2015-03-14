# How is ScavengerEXA different ? #

ScavengerEXA does not participate in the mail conversation. You can use it without running a single mail server. ScavengerEXA simply observes mail conversations passing through a network to detect abnormal mail patterns and looking at the mail meta-data (sender, recipient, source and destination machines). At no point is the mail content itself analysed.

The application can be distributed over many servers to be deployed in large scale networks, with the hope that a large scale deployment would give the industry a new approach to spam fighting and would encourage other ISPs to deploy similar solutions.

# What is wrong with the current solutions ? #

Nothing ! They work ! And without them, email would be simply unusable.

ScavengerEXA attempts to complement the current solutions, not replace them.

All other anti-spam technologies focus on filtering mails at the receiving end, as there are lots of Postmasters willing to pay good money to get rid of spam yet no real business model for doing it at the source.

# Do we need a new approach ? #

Spammers are leveraging their ability to take control of innocent DSL users' machines.

It gives them many "use once throw away" machines used to relay their emails and cause each mail server only to only see a handful of the total volume of spam sent from any single location.

As a result, many unsolicited commercial emails are passing through the net even with today’s most efficient filters.

ScavengerEXA works by analysing the behaviour of the sender. In many respects it is a practical implementation of ideas put forward by [Doctor Richard Clayton](http://www.cl.cam.ac.uk/~rnc1/) with [SpamHINTS](http://www.spamhints.org/).

We just try to stop spam at the source where no one else does.

# How will it change things ? #

The goal of ScavengerEXA is to hit the spammer's **distribution network**, stopping spam like back in the "//good old days//" of open-relays; with the hope that without this abundant, free, distribution network, the spammer's business model will go into recession like any other business whose costs have been driven up.

This is an ambitious goal which will only be possible if the software (or a similar solution) is deployed worldwide.