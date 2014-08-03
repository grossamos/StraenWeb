import cherrypy
import datetime
import json
import mako
import os
import re
import socket
import sqlite3
import sys
import threading
import traceback
import bcrypt

from dateutil.tz import tzlocal
from cherrypy import tools
from mako.lookup import TemplateLookup
from mako.template import Template

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

	def quoteIdentifier(self, s, errors="strict"):
		encodable = s.encode("utf-8", errors).decode("utf-8")
		null_index = encodable.find("\x00")
		if null_index >= 0:
			return ""
		return "\"" + encodable.replace("\"", "\"\"") + "\""

	def create(self):
		try:
			self.execute("create table location (id integer primary key, deviceId integer, activityId integer, latitude double, longitude double, altitude double)")
		except:
			pass

		try:
			self.execute("create table metadata (id integer primary key, deviceId integer, activityId integer, key text, value double)")
		except:
			pass

		try:
			self.execute("create table user (id integer primary key, username text, firstname text, lastname text, hash text)")
		except:
			pass

		try:
			self.execute("create table follower (id integer primary key, userId integer, followerId integer)")
		except:
			pass

		try:
			self.execute("create table device (id integer primary key, device text, userId integer)")
		except:
			pass
	
	def storeUser(self, username, firstname, lastname, hash):
		sql = "insert into user values(NULL, " + self.quoteIdentifier(username) + ", " + self.quoteIdentifier(firstname) + ", " + self.quoteIdentifier(lastname) + ", '" + hash + "')"
		rows = self.execute(sql)
		return rows != None

	def getUserHash(self, username):
		sql = "select hash from user where username = " + self.quoteIdentifier(username)
		rows = self.execute(sql)
		if rows != None and len(rows) > 0:
			return rows[0][0]
		return 0

	def getDeviceId(self, deviceStr):
		sql = "select id from device where device = '" + deviceStr + "'"
		rows = self.execute(sql)
		if len(rows) == 0:
			sql = "insert into device values(NULL, '" + deviceStr + "', 0)"
			rows = self.execute(sql)
			sql = "select id from device where device = '" + deviceStr + "'"
			rows = self.execute(sql)
		return rows[0][0]

	def getLatestActivityId(self, deviceId):
		sql = "select max(activityId) from location where deviceId = " + str(deviceId)
		rows = self.execute(sql)
		if rows != None and len(rows) > 0:
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
		activityId = self.getLatestActivityId(deviceId)
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
		sql = "select count(*) from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
		rows = self.execute(sql)
		if rows != None:
			rowCount = int(rows[0][0])
			newRows = rowCount - num
			if newRows > 0:
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
		activityId = self.getLatestActivityId(deviceId)
		if activityId > 0:
			locations = self.listLocations(deviceId, activityId)
		return locations

class DataListener(threading.Thread):
	def __init__(self, db):
		self.db = db
		self.db.create()
		self.stop = threading.Event()
		self.notMetaData = [ "DeviceId", "ActivityId", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
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
		return None

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

	def authenticateUser(self, username, password):
		if len(username) == 0:
			return False
		if len(password) < 8:
			return False

		dbHash = self.db.getUserHash(username)
		if dbHash == 0:
			return False
		return (dbHash == bcrypt.hashpw(password, dbHash))

	def createUser(self, username, firstname, lastname, password1, password2):
		if len(username) == 0:
			return False
		if len(firstname) == 0:
			return False
		if len(lastname) == 0:
			return False
		if len(password1) < 8:
			return False
		if password1 != password2:
			return False
		if self.db.getUserHash(username) != 0:
			return False

		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(password1, salt)
		return self.db.storeUser(username, firstname, lastname, hash)

class WorkoutsWeb(object):
	def __init__(self, mgr):
		self.mgr = mgr
		super(WorkoutsWeb, self).__init__()

	def terminate():
		self.mgr.listener.stop.set()
		self.mgr = NULL

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def updatetrack(self, deviceStr=None, activityId=None, num=None, *args, **kw):
		if deviceStr is None:
			return ""
		if activityId is None:
			return ""
		if num is None:
			return ""
		
		try:
			deviceId = self.mgr.db.getDeviceId(deviceStr)
			locations = self.mgr.db.listLastLocations(deviceId, activityId, int(num))

			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["

			for location in locations:
				if len(response) > 1:
					response += ","
				response += json.dumps({"latitude":location.latitude, "longitude":location.longitude})

			response += "]"

			return response
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			print "Unexpected error:", sys.exc_info()[0]
			return ""
		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def updatemetadata(self, deviceStr=None, activityId=None, *args, **kw):
		if deviceStr is None:
			return ""
		if activityId is None:
			return ""

		try:
			deviceId = self.mgr.db.getDeviceId(deviceStr)

			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			key = "Name"
			name = self.mgr.db.getLatestMetaData(key, deviceId)
			if name != None:
				response += json.dumps({"name":key, "value":name})

			key = "Time"
			time = self.mgr.db.getLatestMetaData(key, deviceId)
			if time != None:
				localtimezone = tzlocal()
				valueStr = datetime.datetime.fromtimestamp(time/1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":"Sport", "value":valueStr})

			key = "Distance"
			distance = self.mgr.db.getLatestMetaData("Distance", deviceId)
			if distance != None:
				valueStr = "{:.2f}".format(distance)
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":key, "value":valueStr})

			key = "Avg. Speed"
			speed = self.mgr.db.getLatestMetaData("Avg. Speed", deviceId)
			if speed != None:
				valueStr = "{:.2f}".format(speed)
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":key, "value":valueStr})

			key = "Moving Speed"
			speed = self.mgr.db.getLatestMetaData("Moving Speed", deviceId)
			if speed != None:
				valueStr = "{:.2f}".format(speed)
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":key, "value":valueStr})

			key = "Avg. Heart Rate"
			hr = self.mgr.db.getLatestMetaData("Avg. Heart Rate", deviceId)
			if hr != None:
				valueStr = "{:.2f} bpm".format(hr)
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":key, "value":valueStr})

			response += "]"

			return response
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			print "Unexpected error:", sys.exc_info()[0]
			return ""
		return ""

	@cherrypy.expose
	def user(self, deviceStr=None, *args, **kw):
		try:
			deviceId = self.mgr.db.getDeviceId(deviceStr)
			activityId = self.mgr.db.getLatestActivityId(deviceId)
			locations = self.mgr.db.listLocations(deviceId, activityId)
			route = ""
			centerLat = 0
			centerLon = 0

			for location in locations:
				route += "\t\t\t\tnew google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

			if len(locations) > 0:
				centerLat = locations[0].latitude
				centerLon = locations[0].longitude

			myTemplate = Template(filename='map.html', module_directory='tempmod')
			return myTemplate.render(deviceStr=deviceStr, centerLat=centerLat, centerLon=centerLon, route=route, routeLen=len(locations), activityId=str(activityId))
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			print "Unexpected error:", sys.exc_info()[0]
			return ""
		return ""

	@cherrypy.expose
	def login_submit(self, username, password, *args, **kw):
		try:
			if self.mgr.authenticateUser(username, password):
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="Logged in")
			else:
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="Unable to authenticate the user")
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			print "Unexpected error:", sys.exc_info()[0]
		return ""

	@cherrypy.expose
	def create_login_submit(self, username, firstname, lastname, password1, password2, *args, **kw):
		try:
			if self.mgr.createUser(username, firstname, lastname, password1, password2):
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="User created")
			else:
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="Unable to create the user")
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			print "Unexpected error:", sys.exc_info()[0]
		return ""

	@cherrypy.expose
	def login(self):
		myTemplate = Template(filename='login.html', module_directory='tempmod')
		return myTemplate.render()

	@cherrypy.expose
	def create_login(self):
		myTemplate = Template(filename='create_login.html', module_directory='tempmod')
		return myTemplate.render()

	@cherrypy.expose
	def about(self):
		myTemplate = Template(filename='about.html', module_directory='tempmod')
		return myTemplate.render()

	@cherrypy.expose
	def followers(self):
		myTemplate = Template(filename='followers.html', module_directory='tempmod')
		return myTemplate.render()

	@cherrypy.expose
	def index(self):
		deviceStr = "E4F90A14-9763-49FD-B4E0-038D50A3D289"
		return self.user(deviceStr)


mako.collection_size = 100
mako.directories = "templates"

mgr = DataMgr()

conf = {
	'/':
	{
		'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__))},

		'/css':
		{
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'css'
		},

		'/images':
		{
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'images',
		},

		'/media':
		{
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'media',
		}
}

cherrypy.config.update( {'server.socket_host': '0.0.0.0'} )
cherrypy.engine.signals.subscribe()
cherrypy.quickstart(WorkoutsWeb(mgr), config=conf)
