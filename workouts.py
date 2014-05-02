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
				return cur
		except:
			pass
		return None

	def create(self):
		self.execute("create table location (id integer primary key, device text primary key, activityId integer, latitude double, longitude double, altitude double)")

	def storeLocation(self, device, activityId, latitude, longitude, altitude):
		sql = "insert into location values(NULL, '" + device + "', " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
		self.execute(sql)

	def listLocations(self, device, activityId):
		locations = []
		sql = "select latitude, longitude, altitude from location where device = '" + device + "' and activityId = " + str(activityId)
		cur = self.execute(sql)
		rows = cur.fetchall()
		for row in rows:
			location = Location()
			location.latitude = float(row["latitude"])
			location.longitude = float(row["longitude"])
			location.altitude = float(row["altitude"])
			locations.append(location)
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
		except KeyError:
			pass

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
		locations = self.mgr.db.listLocations("", 0)

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
			html += "center: new google.maps.LatLng(" + str(locations[0].latitude) + ", " + str(locations[0].longitude) + "),\n"
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
cherrypy.quickstart(FollowMyWorkout(mgr))
