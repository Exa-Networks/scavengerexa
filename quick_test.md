# Evaluating ScavengerEXA #

## Quick configuration ##

If you do not feel like reading the documentation yet but want to see how scavengerEXA works, you can take it for a ride following those intructions:

Scavenger default configuration is for a single machine installation.

You can change the configuration for a quick test like this :
```
  cd /opt/scavenger/etc/scavenger/
  # Assuming 10.0.0.0/8 and 192.168.0.0/16, the ranges you want to monitor for spam
  echo "10.0.0.0/8 192.168.0.0/16" > capture/internal
  echo "10.0.0.0/8>127.0.0.1:25254" > dispatch/action
  echo "192.168.0.0/16>127.0.0.1:25254" >> dispatch/action
  # 1.2.3.4 the location you are going to redirect spammers (optional)
  echo "1.2.3.4" > dispatch/filter
  # the default settings for the policy daemon should just work (with sqlite3 as database)
  echo "abuse@your.domain.com" > action-mail/recipient
  # The mail server to use as smarthost to send the email notification
  echo "smtp.your.domain.com" > action-mail/smarthost
```

## Quick run ##
```
  cd /opt/scavenger/service
  ./scavenger-action-mail/run 2>&1 > /tmp/action-mail.log &
  ./scavenger-policy/run 2>&1 > /tmp/policy.log &
  ./scavenger-dispatch/run 2>&1 > /tmp/dispatch.log &
  ./scavenger-capture/run 2>&1 > /tmp/capture.log &
```

Note that the capture run scripts will not respond to CTRL-C whilst waiting for data from libpcap.
Don't miss the & sign from the end of the line!

Now, make sure your machine gets a copy of the mail on your network through its eth0 interface (or send a mail if you have the machine IP address within the configure 'internal' range).

If you want to generate traffic to a dummy mail server (to cause invalid conversations, for example, to trigger the spam detection or test a new plugin), you can run the command below.
it will start up a simple SMTP server which dumps received e-mails to the terminal instead of forwarding them on.
```
  python -m smtpd -n -c DebuggingServer 1.2.3.4:25
```