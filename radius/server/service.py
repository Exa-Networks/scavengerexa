import sqlite3

class RadiusDatabase:
	def __init__(self, path):
		self.db = sqlite3.connect(path)

	def trackConnection(self, username, nas, nas_port, ip_addr, route):
		query = "insert into %(table_connections)s (username, nas, nas_port, ip_addr, route) values (?, ?, ?, ?, ?)" % tables
		self.db.insert(query, username, nas, nas_port, ip_addr, route)

	def trackDisconnection(self, username, nas, nas_port, ip_addr, route):
		query = "delete from %(table_connections)s where username = ? and nas = ? and nas_port = ?" % tables
		args = [username, nas, nas_port]

		if ip_addr is not None:
			query += " and ip_addr = ?"
			args.append(ip_addr)

		if route is not None:
			query += " and route = ?"
			args.append(route)

		self.db.delete(query, *args)

	def getConnection(self, ip_addr):
		query = "select (username, nas, nas_port, ip_addr, route) from %(table_connections)s where ip_addr = ? or ? << route" % tables
		self.db.connection.fetchone(query, ip_addr, ip_addr)


class RadiusService:
	def __init__(self, path):
		self.database = RadiusDatabase(path)

	def trackConnection(self, response):
		username = response.get('User-Name', None)
		nas = response.get('NAS-IP-Address', None)
		nas_port = response.get('NAS-Port', None)

		if None in (username, nas, nas_port):
			return None

		ip_addr = response.get('Radius-Framed-IP-Address', None)
		route = response.get('IP-Route', None)

		self.database.trackConnection(username, nas, nas_port, ip_addr, route)

	def trackDisconnection(self, packet):
		username = packet.get('User-Name', None)
		nas = packet.get('NAS-IP-Address', None)
		nas_port = packet.get('NAS-Port', None)

		if None in (username, nas, nas_port):
			return None

		result = self.database.trackDisconnection(username, nas, nas_port)

	def getConnection(self, ip_addr):
		result = self.database.getConnection(ip_addr)
		username = result['username']
		nas = result['nas']
		nas_port = result['nas_port']
		addr = result['ip_addr']
		route = result['route']

		keys = ('User-Name', 'NAS-IP-Address', 'NAS-Port', 'Radius-Framed-IP-Address', 'IP-Route')
		res = (username, nas, nas_port, addr, route)

		return dict(((k,v) for k,v in zip(keys, res) if v is not None))


 # create table users (username text, nas char(15), nas_port char(5), ip_addr char(15), route char(31));
s = RadiusService('/opt/scavenger/db/action_radius')
