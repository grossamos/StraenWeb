import cherrypy
import json
import socket
import sqlite3
import sys
import threading

class Location(object):
	def __init__(self):
		self.latitude = 0.0
		self.longitude = 0.0
		self.altitude = 0.0
		super(Location, self).__init__()

class Database(object):
	def __init__(self):
		super(Database, self).__init__()

	def execute(self, sql):
		try:
			con = sqlite3.connect('workouts.sqlite')
			with con:
				cur = con.cursor()
				cur.execute(sql)
				return cur.fetchall()
		except:
			pass
		finally:
			if con:
				con.close()
		return None

	def create(self):
		try:
			self.execute("create table location (id integer primary key, deviceId integer, activityId integer, latitude double, longitude double, altitude double)")
		except:
			pass

		try:
			self.execute("create table device (id integer primary key, device text)")
		except:
			pass

	def getDeviceId(self, deviceStr):
		sql = "select id from device where device = '" + deviceStr + "'"
		rows = self.execute(sql)
		if len(rows) == 0:
			sql = "insert into device values(NULL, '" + deviceStr + "')"
			rows = self.execute(sql)
			sql = "select id from device where device = '" + deviceStr + "'"
			rows = self.execute(sql)
		return rows[0][0]

	def storeLocation(self, deviceStr, activityId, latitude, longitude, altitude):
		deviceId = self.getDeviceId(deviceStr)
		sql = "insert into location values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
		self.execute(sql)

	def listLocations(self, deviceId, activityId):
		locations = []
		sql = "select latitude, longitude, altitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
		rows = self.execute(sql)
		if rows != None:
			for row in rows:
				location = Location()
				location.latitude = row[0]
				location.longitude = row[1]
				location.altitude = row[2]
				locations.append(location)
		return locations

	def listLocationsForLatestActivity(self, deviceId):
		locations = []
		sql = "select max(activityId) from location where deviceId = " + str(deviceId)
		rows = self.execute(sql)
		if len(rows) > 0:
			activityId = rows[0][0]
			locations = self.listLocations(deviceId, activityId)
		return locations

class DataListener(threading.Thread):
	def __init__(self, db):
		self.db = db
		self.db.create()
		self.stop = threading.Event()
		super(DataListener, self).__init__()

	def terminate():
		self.stop.set()

	def parseJsonStr(self, str):
		try:
			decoder = json.JSONDecoder()
			decodedObj = json.loads(str)
			deviceId = decodedObj["DeviceId"]
			activityId = decodedObj["ActivityId"]
			lat = decodedObj["Latitude"]
			lon = decodedObj["Longitude"]
			alt = decodedObj["Altitude"]
			self.db.storeLocation(deviceId, activityId, lat, lon, alt)
		except ValueError:
			print "ValueError in JSON data."
		except KeyError:
			print "KeyError in JSON data."
		except:
			print "Error in JSON data."

	def readLine(self, sock):
		while not self.stop.is_set():
			data, addr = sock.recvfrom(1024)
			return data
		return ""

	def run(self):
		UDP_IP = ""
		UDP_PORT = 5150

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((UDP_IP, UDP_PORT))

		while not self.stop.is_set():
			line = self.readLine(sock)
			if line:
				self.parseJsonStr(line)

class DataMgr(object):
	def __init__(self):
		self.db = Database()
		self.listener = DataListener(self.db)
		self.listener.start()
		super(DataMgr, self).__init__()

class FollowMyWorkout(object):
	def __init__(self, mgr):
		self.mgr = mgr
		super(FollowMyWorkout, self).__init__()
	
	def index(self):
		deviceId = self.mgr.db.getDeviceId("")
		locations = self.mgr.db.listLocationsForLatestActivity(deviceId)

		html = """

<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />

	<style type="text/css">
		html { height: 100% }
		body { height: 100%; margin: 0; padding: 0 }
		#map-canvas { height: 100% }
	</style>

	<script type="text/javascript"
		src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBhsgYoAKyYFhf3JABWflVMNBDi5tPXvZo&sensor=false">
	</script>

	<script type="text/javascript">
		function initialize()
		{
			var mapOptions =
			{
"""

		if len(locations) > 0:
			lastIndex = len(locations) - 1
			html += "center: new google.maps.LatLng(" + str(locations[lastIndex].latitude) + ", " + str(locations[lastIndex].longitude) + "),\n"
		else:
			html += "center: new google.maps.LatLng(0.0, 0.0),\n"

		html += """
				zoom: 10
			};
			var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

			var flightPlanCoordinates =
			[
"""

		for location in locations:
			str = "new google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"
			html += str

		html += """
			];

			var flightPath = new google.maps.Polyline
			({
				path: flightPlanCoordinates,
				geodesic: true,
				strokeColor: '#FF0000',
				strokeOpacity: 1.0,
				strokeWeight: 2
			});

			flightPath.setMap(map);
		}
		google.maps.event.addDomListener(window, 'load', initialize);
	</script>
	
</head>

<body>
	<div id="map-canvas"/>
</body>

</html>

"""
		return html

	index.exposed = True

mgr = DataMgr()
cherrypy.config.update( {'server.socket_host': '0.0.0.0'} )
cherrypy.quickstart(FollowMyWorkout(mgr))
