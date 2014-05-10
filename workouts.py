import cherrypy
import datetime
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

		try:
			self.execute("create table metadata (id integer primary key, deviceId integer, activityId integer, key text, value double)")
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

	def clearMetadata(self, deviceStr):
		deviceId = self.getDeviceId(deviceStr)
		sql = "delete from metadata where deviceId = " + str(deviceId)
		self.execute(sql)

	def storeMetadata(self, deviceStr, activityId, key, value):
		deviceId = self.getDeviceId(deviceStr)
		sql = "insert into metadata values(NULL, " + str(deviceId) + ", " + str(activityId) + ", '" + key + "', " + str(value) + ")"
		self.execute(sql)

	def getMetaData(self, key, deviceId, activityId):
		try:
			sql = "select value from metadata where key = '" + key + "' and deviceId = " + str(deviceId) + " and activityId = " + str(activityId) + " limit 1"
			rows = self.execute(sql)
			if rows != None:
				return rows[0][0]
		except:
			pass
		return None

	def getLatestMetaData(self, key, deviceId):
		sql = "select max(activityId) from location where deviceId = " + str(deviceId)
		rows = self.execute(sql)
		if len(rows) > 0:
			activityId = rows[0][0]
			return self.getMetaData(key, deviceId, activityId)
		return None

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
		self.notMetaData = [ "DeviceId", "ActivityId", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]
		super(DataListener, self).__init__()

	def terminate():
		self.stop.set()

	def parseJsonStr(self, str):
		try:
			# Parse the location data
			decoder = json.JSONDecoder()
			decodedObj = json.loads(str)
			deviceId = decodedObj["DeviceId"]
			activityId = decodedObj["ActivityId"]
			lat = decodedObj["Latitude"]
			lon = decodedObj["Longitude"]
			alt = decodedObj["Altitude"]
			self.db.storeLocation(deviceId, activityId, lat, lon, alt)

			# Clear the metadata
			self.db.clearMetadata(deviceId)

			# Parse the metadata
			for item in decodedObj.iteritems():
				key = item[0]
				value = item[1]
				if not key in self.notMetaData:
					self.db.storeMetadata(deviceId, activityId, key, value)
		except ValueError:
			print "ValueError in JSON data."
		except KeyError:
			print "KeyError in JSON data."
		except:
			print "Error parsing JSON data."

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

	def terminate():
		self.db = NULL
		self.listener = NULL

class FollowMyWorkout(object):
	def __init__(self, mgr):
		self.mgr = mgr
		super(FollowMyWorkout, self).__init__()

	def terminate():
		self.mgr.listener.stop.set()
		self.mgr = NULL

	def user(self, device=None, *args, **kw):
		deviceId = self.mgr.db.getDeviceId(device)
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
			html += "\tcenter: new google.maps.LatLng(" + str(locations[lastIndex].latitude) + ", " + str(locations[lastIndex].longitude) + "),"
		else:
			html += "\tcenter: new google.maps.LatLng(0.0, 0.0),"
		
		html += """
				zoom: 12
			};
			var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

			var flightPlanCoordinates =
			[\n"""

		for location in locations:
			html += "\t\t\t\tnew google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

		html += """
			];

			"""
		if len(locations) > 0:
			html += """
			var contentString = '<div id="content">' +
			'<div id="siteNotice">' +
			'</div>' +
			'<h1 id="firstHeading" class="firstHeading">Last Known Position</h1>' +
			'<div id="bodyContent">' +
			'<p>"""
			time = self.mgr.db.getLatestMetaData("Time", deviceId)
			if time != None:
				html += datetime.datetime.fromtimestamp(time/1000).strftime('%Y-%m-%d %H:%M:%S')
				html += "<br>"
			distance = self.mgr.db.getLatestMetaData("Distance", deviceId)
			if distance != None:
				html += "Distance = {:.2f}<br>' + '".format(distance)
			hr = self.mgr.db.getLatestMetaData("Avg. Heart Rate", deviceId)
			if hr != None:
				html += "Avg. Heart Rate = {:.2f} bpm<br>' + '".format(hr)
			speed = self.mgr.db.getLatestMetaData("Avg. Speed", deviceId)
			if speed != None:
				html += "Avg. Speed = {:.2f}<br>' + '".format(speed)



			html += "'"
			html += """
			'</p>' +
			'</div>' +
			'</div>';

			var infowindow = new google.maps.InfoWindow
			({
				content: contentString
			});
			
			var marker = new google.maps.Marker
			({
				position: new google.maps.LatLng("""
			html += str(locations[lastIndex].latitude) + ", " + str(locations[lastIndex].longitude) + "),"
			html += """
				map: map,
				title: 'Current Position'
			});
			google.maps.event.addListener(marker, 'click', function()
			{
				infowindow.open(map,marker);
			});
			"""

		html += """
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

	def index(self):
		deviceStr = "E4F90A14-9763-49FD-B4E0-038D50A3D289"
		return self.user(deviceStr)

	user.exposed = True
	index.exposed = True


mgr = DataMgr()
cherrypy.config.update( {'server.socket_host': '0.0.0.0'} )
cherrypy.quickstart(FollowMyWorkout(mgr))
