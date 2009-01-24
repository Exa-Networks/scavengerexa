#!/bin/sh
# Iptables Firewall - created by levy.pl on Wed Dec 14 10:25:19 2005
# Created with ./levy.pl -e eth0 21982
# http://muse.linuxmafia.org/levy
# modified for use with scavenger

# The public IP of the MTA you want to redirect spammers to
MTA=10.0.0.0:25

# chain policies
# set default policies
/sbin/iptables -P INPUT DROP
/sbin/iptables -P OUTPUT ACCEPT
/sbin/iptables -P FORWARD ACCEPT

# flush tables
/sbin/iptables -F
/sbin/iptables -F INPUT
/sbin/iptables -F OUTPUT
/sbin/iptables -F FORWARD
/sbin/iptables -F -t mangle
/sbin/iptables -X
/sbin/iptables -F -t nat

# create DUMP table
/sbin/iptables -N DUMP > /dev/null
/sbin/iptables -F DUMP
/sbin/iptables -A DUMP -p tcp -j REJECT --reject-with tcp-reset
/sbin/iptables -A DUMP -p udp -j REJECT --reject-with icmp-port-unreachable
/sbin/iptables -A DUMP -j DROP

# Stateful table
/sbin/iptables -N STATEFUL > /dev/null
/sbin/iptables -F STATEFUL
/sbin/iptables -I STATEFUL -m state --state ESTABLISHED,RELATED -j ACCEPT
/sbin/iptables -A STATEFUL -j DUMP

# loopback rules
/sbin/iptables -A INPUT -i lo -j ACCEPT
/sbin/iptables -A OUTPUT -o lo -j ACCEPT

# drop reserved addresses incoming
/sbin/iptables -A INPUT -s 127.0.0.0/8 -j DUMP
#/sbin/iptables -A INPUT -s 192.168.0.0/16 -j DUMP
#/sbin/iptables -A INPUT -s 172.16.0.0/12 -j DUMP
#/sbin/iptables -A INPUT -s 10.0.0.0/8 -j DUMP

# allow certain inbound ICMP types
/sbin/iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
/sbin/iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
/sbin/iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
/sbin/iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# opened ports (local machine) by default open ssh
/sbin/iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# exmple of suspended outbound smtp
for i in 127.0.0.2 127.0.0.3; do
	iptables -t nat -A PREROUTING -s $i -p tcp --dport 25  -j DNAT --to-destination $MTA 
	iptables -t nat -A PREROUTING -s $i -p tcp --dport 587 -j DNAT --to-destination $MTA 
done

# push everything else destined to the machine (INPUT) to state table
# packets forwarded through machine (FORWARD) are unaffected
/sbin/iptables -A INPUT -j STATEFUL
