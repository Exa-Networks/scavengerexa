# Running the program #

## In production ##

You will need to have the daemontools program installed.

The ScavengerEXA programs should be controlled by the supervise program. Supervise takes care of running the programs and restarting them should they fail, and connecting the printout of the application to the appropriate log file.

An init.d program is provided to automate the starting of the daemon.

It can be started with:
```
  /opt/scavenger/service/scavenger start
```
And be stopped with:
```
  /opt/scavenger/service/scavenger stop
```
## The manual way ##

A way to test each program is to call it via its 'run script' located in the ScavengerEXA service directory. The run scripts are designed to be run from the supervise program but can be called from the shell.

For example to invoke the capture program you could run:
```
  [thomas@scavenger]# /opt/scavenger/service/scavenger-capture-pcap/run 
```
with a debug level of 0 you should see something like:
```
  Psyco is not available
  listening on eth0: tcp and port 25
```
## The hard way ##

Should you want to gain more control on the way the program is run, all ScavengerEXA applications designed to run in the background (such as the capture program) are located in the daemon directory.
```
  [thomas@scavenger]# ls /opt/scavenger/daemon/
  action-mail.py*  action-netfilter.py*  capture-pcap.py*  dispatch.py*  mta.py*  policy.py*
```
The scavenger library is located in the lib folder, and should be in the python include path.

This can be achieved by copying the lib/scavenger folder into your python site-package directory, or adding this folder to the PYTHONPATH.

So in order to test the capture application with the default configuration you could try:
```
  env \
  ETC=/opt/scavenger/etc/ \
  PYTHONPATH=$PYTHONPATH:/opt/scavenger/lib \
  python /opt/scavenger/daemon/capture-pcap.py
```
which should start the application just as the run script did.

You can test various configuration changes on the command line without changing the configuration file by using the environment values, for example to change the debug level from 0 to 1 you could enter:
```
  env \
  ETC=/opt/scavenger/etc/ \
  PYTHONPATH=$PYTHONPATH:/opt/scavenger/lib \
  debug=1 \
  python /opt/scavenger/daemon/capture-pcap.py
```
Which would give an ouput similar to (depending on your current settings):
```
  Psyco is not available
  ********************************************************************************
  diffusion            : rr
  promiscuous          : False
  dispatch             : [('127.0.0.1', 25252)]
  interface            : eth0
  internal             : [('82.219.192.0', 18), ('82.219.9.0', 24)]
  debug                : 1
  ********************************************************************************
  debug parser False
  debug cache  False
  debug udp    False
  debug wire   False
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  listening on eth0: tcp and port 25
```