import cherrypy
import datetime
import json
import os
import socket
import sqlite3
import sys
import threading

MEDIA_DIR = os.path.join(os.path.abspath("."), u"media")

class Location(object):
	def __init__(self):
		self.latitude = 0.0
		self.longitude = 0.0
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

	def GetLatestActivityId(self, deviceId):
		sql = "select max(activityId) from location where deviceId = " + str(deviceId)
		rows = self.execute(sql)
		if len(rows) > 0:
			return rows[0][0]
		return 0

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
		activityId = self.GetLatestActivityId(deviceId)
		if activityId > 0:
			return self.getMetaData(key, deviceId, activityId)
		return None

	def storeLocation(self, deviceStr, activityId, latitude, longitude, altitude):
		deviceId = self.getDeviceId(deviceStr)
		sql = "insert into location values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
		self.execute(sql)

	def listLocations(self, deviceId, activityId):
		locations = []
		sql = "select latitude, longitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
		rows = self.execute(sql)
		if rows != None:
			for row in rows:
				location = Location()
				location.latitude = row[0]
				location.longitude = row[1]
				locations.append(location)
		return locations

	def listLastLocations(self, deviceId, activityId, num):
		locations = []
		sql = "select latitude, longitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId) + " order by id desc limit " + str(num)
		rows = self.execute(sql)
		if rows != None:
			for row in rows:
				location = Location()
				location.latitude = row[0]
				location.longitude = row[1]
				locations.append(location)
		return locations

	def listLocationsForLatestActivity(self, deviceId):
		locations = []
		activityId = self.GetLatestActivityId(deviceId)
		if activityId > 0:
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
		sock.close()

	def parseJsonStr(self, str):
		try:
			decoder = json.JSONDecoder()
			decodedObj = json.loads(str)

			# Parse the location data
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
		except KeyError, e:
			print "KeyError - reason " + str(e) + "."
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

class WorkoutsWeb(object):
	def __init__(self, mgr):
		self.mgr = mgr
		super(WorkoutsWeb, self).__init__()

	def terminate():
		self.mgr.listener.stop.set()
		self.mgr = NULL

	def update(self, deviceStr=None, activityId=None, num=None, *args, **kw):
		if deviceStr is None:
			return ""
		if activityId is None:
			return ""
		if num is None:
			return ""

		try:
			deviceId = self.mgr.db.getDeviceId(deviceStr)
			locations = self.mgr.db.listLocationsForLatestActivity(deviceId)

			html = ""
			for i in range(num, len(locations) - 1):
				html += json.dumps({"latitude":locations[i].latitude, "longitude":locations[i].longitude}) + "\n"
			return html
		except:
			return ""
		return ""

	def user(self, deviceStr=None, *args, **kw):
		try:
			deviceId = self.mgr.db.getDeviceId(deviceStr)
			activityId = self.mgr.db.GetLatestActivityId(deviceId)
			locations = self.mgr.db.listLocations(deviceId, activityId)

			html = """
<!DOCTYPE html>
<html>

<head>
	<title>Live Tracking</title>

	<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />

	<style type="text/css">
		html { height: 100% }
		body { height: 100%; margin: 0; padding: 0 }
		#map-canvas { height: 100% }
	</style>

	<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script>
	<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBhsgYoAKyYFhf3JABWflVMNBDi5tPXvZo&sensor=false"></script>

	<script type="text/javascript">
		var routeCoordinates
		var contentString
		var routePath

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

			routeCoordinates =
			[\n"""

			for location in locations:
				html += "\t\t\t\tnew google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

			html += """
			];

			"""
			if len(locations) > 0:
				html += """
			contentString = '<div id="content">' +
				'<div id="siteNotice">' +
				'</div>' +
				'<h2 id="firstHeading" class="firstHeading">Last Known Position</h2>' +
				'<div id="bodyContent">' +
				'<p>"""
				time = self.mgr.db.getLatestMetaData("Time", deviceId)
				if time != None:
					html += datetime.datetime.fromtimestamp(time/1000).strftime('%Y-%m-%d %H:%M:%S %Z')
					html += "<br>"
				distance = self.mgr.db.getLatestMetaData("Distance", deviceId)
				if distance != None:
					html += "Total Distance = {:.2f}<br>".format(distance)
				speed = self.mgr.db.getLatestMetaData("Avg. Speed", deviceId)
				if speed != None:
					html += "Avg. Speed (Includes Stops) = {:.2f}<br>".format(speed)
				speed = self.mgr.db.getLatestMetaData("Moving Speed", deviceId)
				if speed != None:
					html += "Moving Speed = {:.2f}<br>".format(speed)
				hr = self.mgr.db.getLatestMetaData("Avg. Heart Rate", deviceId)
				if hr != None:
					html += "Avg. Heart Rate = {:.2f} bpm<br>".format(hr)
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

			infowindow.open(map,marker);
			"""

			html += """
			routePath = new google.maps.Polyline
			({
				path: routeCoordinates,
				geodesic: true,
				strokeColor: '#FF0000',
				strokeOpacity: 1.0,
				strokeWeight: 2
			});

			routePath.setMap(map);
		}

		google.maps.event.addDomListener(window, 'load', initialize);

		var processUpdates = function(response)
		{
			console.log(response)
			if (response != null)
			{
				lines = response.split("\\n")
				for (var i = 0; i < lines.length; i++)
				{
					var obj = JSON.parse(lines[i]);
				//	var path = routePath.getPath();
				//	routeCoordinates.push(new google.maps.LatLng(-27.46758, 153.027892));
				//	routePath.setPath(routeCoordinates);
				//	routePath.setMap(map);
				}
			}
		};

		var checkForUpdates = function()
		{
			$.ajax({ url: "update/""" + deviceStr + "/" + str(activityId) + """/\" + routeCoordinates.length, success: processUpdates, dataType: "json" });
		};
		setInterval(checkForUpdates, 5000);
	</script>

</head>

<body>
	<div id="map-canvas"/>
</body>

</html>

"""
			return html
		except:
			return ""
		
		return ""

	def index(self):
		deviceStr = "E4F90A14-9763-49FD-B4E0-038D50A3D289"
		return self.user(deviceStr)

	update.exposed = True
	user.exposed = True
	index.exposed = True

	config = { '/media':
		{	'tools.staticdir.on': True,
			'tools.staticdir.dir': MEDIA_DIR,
		}
	}

mgr = DataMgr()
cherrypy.config.update( {'server.socket_host': '0.0.0.0'} )
cherrypy.quickstart(WorkoutsWeb(mgr))
