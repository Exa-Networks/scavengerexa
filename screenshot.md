# Screenshot #

As everyone likes screenshots to have an idea of how an application works, here are some edited captures.

# Capture #
```
  [root@sp-fw-1 scavenger]# ./service/scavenger-capture-pcap/run 
  Psyco is not available
  ********************************************************************************
  debug                : 9
  slow                 : False
  diffusion            : rr
  promiscuous          : False
  interface            : eth0
  internal             : ['82.219.192.0/18', '82.219.9.0/24']
  dispatch             : [('127.0.0.1', 25252)]
  ********************************************************************************
  debug parser False
  debug cache  False
  debug udp    True
  debug wire   False
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  listening on eth0: tcp and port 25
  co=250
  di=209.181.247.105
  rc=0
  st=EHLO
  re=
  si=82.219.202.49
  in=01.c955.3f.3caf
  or=pcap
  se=
  he=uk.whitehouse.org
    
  co=250
  di=209.181.247.105
  rc=0
  st=MAIL
  re=
  si=82.219.202.49
  in=01.c955.3f.3caf
  or=pcap
  se=obama@whitehouse.org
  he=uk.whitehouse.org
```
# Dispatch #
```
  [root@sp-fw-1 scavenger]# ./service/scavenger-dispatch/run 
  Psyco is not available
  ********************************************************************************
  debug                : 1
  slow                 : False
  policy               : [('127.0.0.1', 25253)]
  filter               : ['82.219.2.81']
  action               : {(1390084096, 1390149631): [('127.0.0.1', 25254)]}
  time                 : 21600
  validate             : False
  ********************************************************************************
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  [      0] 82.219.202.49   dispatching message to 127.0.0.1:25253
  [      0] 82.219.202.49   policy answers HAM
  [      1] 82.219.202.49   dispatching message to 127.0.0.1:25253
  [      1] 82.219.202.49   policy answers HAM
```
## Policy ##
```
  2009/01/24 00:42 +0100 [-] Psyco is not available
  2009/01/24 00:42 +0100 [-] ********************************************************************************
  2009/01/24 00:42 +0100 [-] configuration is /opt/scavenger/etc/scavenger/policy/scavenger.conf
  2009/01/24 00:42 +0100 [-]   * database_prefix = scavenger
  2009/01/24 00:42 +0100 [-]   * database_path   = /opt/scavenger/db/
  2009/01/24 00:42 +0100 [-]   * database_port   = 3306
  2009/01/24 00:42 +0100 [-]   * thread          = 200
  2009/01/24 00:42 +0100 [-]   * ip              = 127.0.0.1
  2009/01/24 00:42 +0100 [-]   * acl             = ['127.0.0.1', '192.168.0.0/24']
  2009/01/24 00:42 +0100 [-]   * database_password = password
  2009/01/24 00:42 +0100 [-]   * api             = sqlite3
  2009/01/24 00:42 +0100 [-]   * database_host   = 127.0.0.1
  2009/01/24 00:42 +0100 [-]   * database_user   = user
  2009/01/24 00:42 +0100 [-]   * timeout         = 60
  2009/01/24 00:42 +0100 [-]   * plugins         = ['ratio', 'helo']
  2009/01/24 00:42 +0100 [-]   * debug           = 0
  2009/01/24 00:42 +0100 [-]   * message         = 
  2009/01/24 00:42 +0100 [-]   * type            = scavenger
  2009/01/24 00:42 +0100 [-]   * port            = 25253
  2009/01/24 00:42 +0100 [-]   * pidfile         = /var/run/scavenger-scavenger.pid
  2009/01/24 00:42 +0100 [-] ********************************************************************************
  2009/01/24 00:42 +0100 [-] initialisation of plugin helo
  2009/01/24 00:42 +0100 [-]   * reading configuration file
  2009/01/24 00:42 +0100 [-]   * running plugin initialisation
  2009/01/24 00:42 +0100 [-]   * complete
  2009/01/24 00:42 +0100 [-] initialisation of plugin ratio
  2009/01/24 00:42 +0100 [-]   * reading configuration file
  2009/01/24 00:42 +0100 [-]   * running plugin initialisation
  2009/01/24 00:42 +0100 [-]   * complete
  2009/01/24 00:42 +0100 [-] --------------------------------------------------------------------------------
  2009/01/24 00:42 +0100 [-] skipping uncalled plugin deny
  2009/01/24 00:42 +0100 [-] skipping uncalled plugin spread
  2009/01/24 00:42 +0100 [-] skipping uncalled plugin allow
  2009/01/24 00:42 +0100 [-] calling cleanup for helo
  2009/01/24 00:42 +0100 [-] calling cleanup for ratio
  2009/01/24 00:42 +0100 [-] ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  2009/01/24 00:42 +0100 [-] twisted.protocols.policies.TimeoutFactory starting on 25253
  2009/01/24 00:42 +0100 [-] Starting factory <scavenger.policy.factory.MailPolicyFactoryFromService instance at 0xb75b904c>
  2009/01/24 00:42 +0100 [-] Starting factory <twisted.protocols.policies.TimeoutFactory instance at 0xb76511ac>
  2009/01/24 00:42 +0100 [-] 82.219.202.49   HELO : HAM
  2009/01/24 00:42 +0100 [-] 82.219.202.49   MAIL : HAM
```
# Action Mail #
```
  [root@sp-fw-1 scavenger]# ./service/scavenger-action-mail/run 
  Psyco is not available
  ********************************************************************************
  debug                : 7
  slow                 : False
  port                 : 25254
  timeout              : 60
  smarthost            : smtp.exa-networks.co.uk
  sender               : <scavenger-action@sp-fw-1.tcm.exa.org.uk> ScavengerEXA
  recipient            : <thomas.mangin@exa-networks.co.uk> Thomas Mangin
  ********************************************************************************
  ip=82.219.123.456  act=FILTER  dest=0.0.0.0:00000         dur=86400 msg="mail sent to a blocked address <user@domain.com>"
  no email sent in debug mode
```