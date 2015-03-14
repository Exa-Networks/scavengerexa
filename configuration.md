# Configuring ScavengerEXA #

## Quick Configuration ##

You can quickly configure ScavengerEXA to evaluate it by following [those instructions](http://code.google.com/p/scavengerexa/wiki/quick_test).

## Controlling ScavengerEXA ##

How to get Scavenger to [start at boot time](http://code.google.com/p/scavengerexa/wiki/running) or how to [run each scavenger program](http://code.google.com/p/scavengerexa/wiki/running) from the command line (in order to test a configuration change for example).

## Configuration Options ##

A list of the possible configuration options for each application:

  * [Capture program](http://code.google.com/p/scavengerexa/wiki/configuration_capture)
  * [Dispatch Server](http://code.google.com/p/scavengerexa/wiki/configuration_dispatch)
  * [Policy Server](http://code.google.com/p/scavengerexa/wiki/configuration_policy)
  * [Mail Action Server](http://code.google.com/p/scavengerexa/wiki/configuration_action-mail)
  * [Netfilter Action Server](http://code.google.com/p/scavengerexa/wiki/configuration_action-netfilter)

## Where are the configuration files ##

The configuration files are located in the the etc/ folder of the scavenger repository in a folder named scavenger.
Each application has its own subfolder in this location.
```
  [thomas@scavenger]# ls /opt/scavenger/etc/scavenger/
  action-mail/  action-netfilter/  capture-pcap/  dispatch/  policy/
```
Each application learns the location of this folder from the ETC environment value. You can therefore change the location of the scavenger/etc folder to suit your needs.
```
  [thomas@scavenger]# echo -e "import os\nprint 'etc is', os.environ.get('ETC','not defined')\n"   env ETC=/opt/scavenger/etc/ python
  etc is /opt/scavenger/etc/
```