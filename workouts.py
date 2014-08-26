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

SESSION_KEY = '_cp_username'

def check_auth(*args, **kwargs):
	# A tool that looks in config for 'auth.require'. If found and it is not None, a login
	# is required and the entry is evaluated as a list of conditions that the user must fulfill
	conditions = cherrypy.request.config.get('auth.require', None)
	if conditions is not None:
		username = cherrypy.session.get(SESSION_KEY)
		if username:
			cherrypy.request.login = username
			for condition in conditions:
				# A condition is just a callable that returns true or false
				if not condition():
					raise cherrypy.HTTPRedirect("/login")
		else:
			raise cherrypy.HTTPRedirect("/login")

def require(*conditions):
	# A decorator that appends conditions to the auth.require config variable.
	def decorate(f):
		if not hasattr(f, '_cp_config'):
			f._cp_config = dict()
		if 'auth.require' not in f._cp_config:
			f._cp_config['auth.require'] = []
		f._cp_config['auth.require'].extend(conditions)
		return f
	return decorate

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
		if username is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if firstname is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if lastname is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if hash is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if len(username) == 0:
			cherrypy.log.error("username too short")
			return
		if len(firstname) == 0:
			cherrypy.log.error("firstname too short")
			return
		if len(lastname) == 0:
			cherrypy.log.error("lastname too short")
			return
		if len(hash) == 0:
			cherrypy.log.error("hash too short")
			return

		try:
			sql = "insert into user values(NULL, " + self.quoteIdentifier(username) + ", " + self.quoteIdentifier(firstname) + ", " + self.quoteIdentifier(lastname) + ", '" + hash + "')"
			rows = self.execute(sql)
			return rows != None
		except:
			pass
		return None

	def getUserHash(self, username):
		if username is None:
			cherrypy.log.error("Unexpected empty object")
			return 0
		if len(username) == 0:
			cherrypy.log.error("username too short")
			return 0

		try:
			sql = "select hash from user where username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def getUserIdFromUserName(self, username):
		if username is None:
			cherrypy.log.error("Unexpected empty object")
			return 0
		if len(username) == 0:
			cherrypy.log.error("username too short")
			return 0

		try:
			sql = "select id from user where username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def getDeviceIdFromDeviceStr(self, deviceStr):
		if deviceStr is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if len(deviceStr) == 0:
			cherrypy.log.error("username too short")
			return None

		try:
			sql = "select id from device where device = " + self.quoteIdentifier(deviceStr)
			rows = self.execute(sql)
			if len(rows) == 0:
				sql = "insert into device values(NULL, " + self.quoteIdentifier(deviceStr) + ", 0)"
				rows = self.execute(sql)
				sql = "select id from device where device = " + self.quoteIdentifier(deviceStr)
				rows = self.execute(sql)
			return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def getDeviceIdFromUsername(self, username):
		if username is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if len(username) == 0:
			cherrypy.log.error("username too short")
			return None

		try:
			sql = "select device.id from device inner join user on device.userId=user.id and user.username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if len(rows) == 0:
				sql = "insert into device values(NULL, " + self.quoteIdentifier(deviceStr) + ", 0)"
				rows = self.execute(sql)
				sql = "select id from device where device = " + self.quoteIdentifier(deviceStr)
				rows = self.execute(sql)
			return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def getLatestActivityId(self, deviceId):
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		try:
			sql = "select max(activityId) from location where deviceId = " + str(deviceId)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return 0

	def clearMetadata(self, deviceStr):
		if deviceStr is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			cherrypy.log.error("deviceStr too short")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			sql = "delete from metadata where deviceId = " + str(deviceId)
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return

	def storeMetadata(self, deviceStr, activityId, key, value):
		if deviceStr is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if activityId is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if key is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if value is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			cherrypy.log.error("deviceStr too short")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			sql = "insert into metadata values(NULL, " + str(deviceId) + ", " + str(activityId) + ", '" + key + "', " + str(value) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return

	def getMetaData(self, key, deviceId, activityId):
		if key is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if activityId is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		try:
			sql = "select value from metadata where key = " + self.quoteIdentifier(key) + " and deviceId = " + str(deviceId) + " and activityId = " + str(activityId) + " limit 1"
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def getLatestMetaData(self, key, deviceId):
		if key is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		try:
			activityId = self.getLatestActivityId(deviceId)
			if activityId > 0:
				return self.getMetaData(key, deviceId, activityId)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return None

	def storeLocation(self, deviceStr, activityId, latitude, longitude, altitude):
		if deviceStr is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if activityId is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if latitude is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if longitude is None:
			cherrypy.log.error("Unexpected empty object")
			return
		if altitude is None:
			cherrypy.log.error("Unexpected empty object")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			sql = "insert into location values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return

	def listLocations(self, deviceId, activityId):
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if activityId is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select latitude, longitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
			rows = self.execute(sql)
			if rows != None:
				for row in rows:
					location = Location()
					location.latitude = row[0]
					location.longitude = row[1]
					locations.append(location)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return locations

	def listLastLocations(self, deviceId, activityId, num):
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if activityId is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if num is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select count(*) from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
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
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return locations

	def listLocationsForLatestActivity(self, deviceId):
		if deviceId is None:
			cherrypy.log.error("Unexpected empty object")
			return None

		locations = []

		try:
			activityId = self.getLatestActivityId(deviceId)
			if activityId > 0:
				locations = self.listLocations(deviceId, activityId)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return locations

	def listUsersFollowed(self, username):
		if username is None:
			cherrypy.log.error("Unexpected empty object")
			return None
		if len(username) == 0:
			cherrypy.log.error("username too short")
			return None

		followers = []

		try:
			userId = self.getUserIdFromUserName(username)
		except:
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return followers

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
	_cp_config = {
		'tools.sessions.on': True,
		'tools.auth.on': True
	}

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
			deviceId = self.mgr.db.getDeviceIdFromDeviceStr(deviceStr)
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
			cherrypy.log.error(sys.exc_info()[0])
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
			deviceId = self.mgr.db.getDeviceIdFromDeviceStr(deviceStr)

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
				response += json.dumps({"name":"Time", "value":valueStr})

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
			cherrypy.log.error(sys.exc_info()[0])
			return ""
		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def listUsersFollowed(self, username=None, num=None, *args, **kw):
		if username is None:
			return ""

		try:
			followers = self.mgr.db.listUsersFollowed(username)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":username})

			response += "]"
			
			return response
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
			return ""
		return ""

	@cherrypy.expose
	def user(self, deviceStr=None, *args, **kw):
		try:
			deviceId = self.mgr.db.getDeviceIdFromDeviceStr(deviceStr)
			activityId = self.mgr.db.getLatestActivityId(deviceId)
			locations = self.mgr.db.listLocations(deviceId, activityId)

			if len(locations) == 0:
				myTemplate = Template(filename='auth_error.html', module_directory='tempmod')
				return myTemplate.render(error="There is no data for the specified user.")
				
			route = ""
			centerLat = 0
			centerLon = 0

			for location in locations:
				route += "\t\t\t\tnew google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

			if len(locations) > 0:
				centerLat = locations[0].latitude
				centerLon = locations[0].longitude

			myTemplate = Template(filename='map_single.html', module_directory='tempmod')
			return myTemplate.render(deviceStr=deviceStr, centerLat=centerLat, centerLon=centerLon, route=route, routeLen=len(locations), activityId=str(activityId))
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
			return ""
		return ""

	@cherrypy.expose
	@require()
	def following(self, username=None, *args, **kw):
		try:
			followers = self.mgr.db.listUsersFollowed(username)
			for follower in followers:
				pass

#			myTemplate = Template(filename='map_multi.html', module_directory='tempmod')
#			return myTemplate.render()
			myTemplate = Template(filename='error.html', module_directory='tempmod')
			return myTemplate.render(error="foo.")
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return ""

	@cherrypy.expose
	def login_submit(self, username, password, *args, **kw):
		try:
			if self.mgr.authenticateUser(username, password):
				cherrypy.session.regenerate()
				cherrypy.session[SESSION_KEY] = cherrypy.request.login = username
				return self.following(username)
			else:
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="Unable to authenticate the user.")
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
		return ""

	@cherrypy.expose
	def create_login_submit(self, username, firstname, lastname, password1, password2, *args, **kw):
		try:
			if self.mgr.createUser(username, firstname, lastname, password1, password2):
				return self.following(username)
			else:
				myTemplate = Template(filename='error.html', module_directory='tempmod')
				return myTemplate.render(error="Unable to create the user.")
		except:
			cherrypy.response.status = 500
			traceback.print_exc(file=sys.stdout)
			cherrypy.log.error(sys.exc_info()[0])
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

cherrypy.config.update( {
					   'server.socket_host': '0.0.0.0',
					   'log.access_file': "workouts_error.log",
					   'log.error_file': "workouts_access.log" } )
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)
cherrypy.engine.signals.subscribe()
cherrypy.quickstart(WorkoutsWeb(mgr), config=conf)
