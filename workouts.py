import cherrypy
import json
import socket
import sqlite3
import threading

class Database(object):
	def __init__(self):
		self.con = sqlite3.connect('workouts.db')

	def create(self):
		with self.con:
			self.cur = self.con.cursor()
			self.cur.execute("create table location (device text primary key, activityId integer, latitude double, longitude double, altitude double)")

	def storeLocation(self, device, activityId, latitude, longitude, altitude):
		with self.con:
			sql = "insert into location values(" + device + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
			self.cur.execute(sql)

class DataListener(threading.Thread):
	def __init__(self, db):
		self.db = db

	def parseJsonStr(self, str):
		pass

	def readLine(self, sock):
		line = ""

		while True:
			d = sock.recvfrom(1)
			data = d[0]
			addr = d[1]

			if not data:
				break

		return line

	def run(self):
		UDP_IP = "127.0.0.1"
		UDP_PORT = 5150

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((UDP_IP, UDP_PORT))

		while True:
			line = self.readLine(sock)
			if line:
				self.parseJsonStr(line)

class DataMgr(object):
	def __init__(self):
		self.db = Database()
		self.listener = DataListener()
		self.listener.start()

class FollowMyWorkout(object):
	def index(self):
		return """

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
				center: new google.maps.LatLng(-34.397, 150.644),
				zoom: 10
			};
			var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

			var flightPlanCoordinates =
			[
				new google.maps.LatLng(37.772323, -122.214897),
				new google.maps.LatLng(21.291982, -157.821856),
				new google.maps.LatLng(-18.142599, 178.431),
				new google.maps.LatLng(-27.46758, 153.027892)
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

	index.exposed = True

mgr = DataMgr()
cherrypy.quickstart(FollowMyWorkout())
