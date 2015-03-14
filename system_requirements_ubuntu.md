# System Requirements for Ubuntu 8.04 #

Download and install [Ubuntu](http://www.ubuntu.com/getubuntu/download) for server

# Log with root privileges #
```
  login: username
  password: password
  
  # sudo bash
  password: password
```
# Make sure your OS is up to date #
```
  # apt-get update
  # apt-get upgrade
```
# Install Dependencies #

## twisted ##

If you are going to run anything other than scavenger-capture, you need [twisted](http://twistedmatrix.com/trac/).
```
  # apt-get install python-twisted
  # apt-get install twisted-doc
```
## daemontools ##

[Deamontools](http://cr.yp.to/daemontools.html) is not mandatory, but recommended. you can use upstart or systemd instead.
```
  # apt-get install build-essential
  # apt-get install debhelper html2text po-debconf po-debconf gettext intltool-debian
  
  # wget http://uk.archive.ubuntu.com/ubuntu/pool/multiverse/d/daemontools-installer/daemontools-installer_0.76-9.2_all.deb
  # dpkg -i daemontools-installer_0.76-9.2_all.deb
  
  # touch /etc/inittab
  # cd /usr
  # ln -s /usr/share/man .
  
  # get-daemontools
  # build-daemontools
```
use option F(hs) for the file layout.

## scavenger-capture required packages ##

If you wish to run the scavenger-capture module, you will need to install the python-libpcap and python-pypcap packages.
```
  # apt-get install python2.5-libpcap
  # apt-get install python2.5-pypcap
```
Due to [bug 304086](https://bugs.launchpad.net/ubuntu/+source/python-pypcap/+bug/304086) we have to install dpkt from source.

```
  # wget http://dpkt.googlecode.com/files/dpkt-1.6.tar.gz
  # tar zxvf dpkt-1.6.tar.gz
  # cd dpkt-1.6
  # python setup.py install
  # cd -
  # rm -rf dpkt-1.6
  # rm dpkt-1.6.tar.gz
```

## scavenger-action-netfilter required packages ##

If you wish to run the scavenger-netfilter module, you will need to install the python-netfilter package.
```
  # wget http://opensource.bolloretelecom.eu/files/python-netfilter-0.5.5.tar.gz
  # tar zxvf python-netfilter-0.5.5.tar.gz
  # cd python-netfilter-0.5.5
  # python setup.py install
  # cd -
  # rm -rf python-netfilter-0.5.5
  # rm python-netfilter-0.5.5.tar.gz
```

# To contribute #

We would be delighted if you could contribute to the project!
```
  # apt-get install mercurial
```

Done :)