import cherrypy
import json
import socket
import sqlite3
import threading

class DataListener(threading.Thread):
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

class FollowMyWorkout(object):
	def index(self):
		return """

<!DOCTYPE html>

<html>
	<head>

		<style>
			#map_canvas
			{
				width: 640px;
				height: 480px;
			}
		</style>

		<script src="https://maps.googleapis.com/maps/api/js?sensor=false"></script>
		<script>
			function initialize()
			{
				var map_canvas = document.getElementById('map_canvas');
				var map_options =
				{
					center/Users/mike: new google.maps.LatLng(0, -180),
					zoom: 4,
					mapTypeId: google.maps.MapTypeId.ROADMAP
				}
				var map = new google.maps.Map(map_canvas, map_options)

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
		<div id="map_canvas"></div>
	</body>

</html>

"""

	index.exposed = True

cherrypy.quickstart(FollowMyWorkout())
