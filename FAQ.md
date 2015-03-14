# FAQ #

No, no one asked these question yet, but here are the answers anyway :-D

**Why is it called ScavengerEXA ?**

  * As it is a carnivore http://en.wikipedia.org/wiki/Carnivore_(FBI)
  * which eats your network Junk http://en.wikipedia.org/wiki/Spam_(electronic)
  * And as it was developed by Exa Networks Limited http://en.wikipedia.org/wiki/Exa-


**What are the dependencies for this program**

  * Python, tested with version 2.5.2 http://www.python.org/download/releases/2.5.2/
  * Twisted Matrix, event-driven networking engine http://twistedmatrix.com/
  * the packet capture library (pcap) http://pypi.python.org/pypi/pcap/
  * the dump packet module (dpkt)http://pypi.python.org/pypi/dpkt/
  * optional for policy, MySQL http://mysql.org/ with the python MySQLdb modules http://mysql-python.sourceforge.net/
  * optional for policy, PosgreSQL http://www.postgresql.org with the pg8000 module http://pybrary.net/pg8000/
  * optional for action-netfilter, python netfilter http://opensource.bolloretelecom.eu/projects/python-netfilter/
  * optional djb daemontools http://cr.yp.to/daemontools.html


**What database can I use for the policy server ?**

  * Do NOT use sqlite3 as production database
  * but it can be used to evaluate the software

  * The policy server uses the Python Database API Specification v2.0 http://www.python.org/dev/peps/pep-0249/
  * so it should trivial to port it to any DB with a DB-API2 interface.
  * sqlite3 and MySQL have been tested, postgresql should just work
  * If you are going to use MySQL you may want to read this article http://lucumr.pocoo.org/2009/1/8/the-sad-state-of-mysql-python
  * If you are planning on testing postgresql look at this module  http://pybrary.net/pg8000/


**What OS is this designed to run on ?**

  * The main development is done under Linux (both Redhat and Ubuntu)
  * We have no idea if this runs correctly on other Unix flavors.


**What licence is the code released under ?**

  * This code is released under the affero GPL licence v 3.0 http://www.gnu.org/licenses/agpl-3.0.txt.
  * Please note that this is the 3.0 only and not any later version (no-one has checked possible license incompatibility issues yet).


**Who holds the copyright for the code ?**

  * Thomas Mangin wrote most of the code whilst working for Exa Networks Ltd.http://www.exa-networks.co.uk/
  * His collegue David Farrar provided a large amount of help not necessarily correctly expressed in the copyright note added later.


**Can I contribute ?**

  * Sure, send us patches or ideas.
  * We may need you to send a signed copyright transfer, but as no-one has done it yet we have not decided.


**Do your require copyright assignment ?**

  * No, you can keep the copyright of the code you provide as long as you use the project licence.