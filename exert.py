import cherrypy
import datetime
import json
import mako
import os
import re
import signal
import sys
import bcrypt
import ExertDb

from random import randint
from dateutil.tz import tzlocal
from cherrypy import tools
from cherrypy.process.plugins import Daemonizer
from mako.lookup import TemplateLookup
from mako.template import Template

g_rootDir               = os.path.dirname(os.path.abspath(__file__))
g_rootUrl               = 'http://exert-app.com/live'
g_accessLog             = 'exert_access.log'
g_exertLog              = 'exert_error.log'
g_tempmodDir            = os.path.join(g_rootDir, 'tempmod')
g_loginHtmlFile         = os.path.join(g_rootDir, 'login.html')
g_createLoginHtmlFile   = os.path.join(g_rootDir, 'create_login.html')
g_mapSingleHtmlFile     = os.path.join(g_rootDir, 'map_single.html')
g_errorHtmlFile         = os.path.join(g_rootDir, 'error.html')
g_errorLoggedInHtmlFile = os.path.join(g_rootDir, 'error_logged_in.html')
g_aboutHtmlFile         = os.path.join(g_rootDir, 'about.html')
g_app                   = None

SESSION_KEY = '_cp_username'
MIN_PASSWORD_LEN = 8

def signal_handler(signal, frame):
	global g_app
	print "Exiting..."
	if g_app is not None:
		g_app.terminate()
	sys.exit(0)

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

class DataMgr(object):
	def __init__(self):
		self.db = ExertDb.Database(g_rootDir)
		super(DataMgr, self).__init__()

	def terminate(self):
		self.db = None

	def authenticateUser(self, username, password):
		if len(username) == 0:
			return False
		if len(password) < MIN_PASSWORD_LEN:
			return False

		dbHash = self.db.getUserHash(username)
		if dbHash == 0:
			return False
		return (dbHash == bcrypt.hashpw(password, dbHash))

	def createUser(self, username, firstname, lastname, password1, password2, deviceStr):
		if len(username) == 0:
			return False
		if len(firstname) == 0:
			return False
		if len(lastname) == 0:
			return False
		if len(password1) < MIN_PASSWORD_LEN:
			return False
		if password1 != password2:
			return False
		if self.db.getUserHash(username) != 0:
			return False
		if len(deviceStr) == 0:
			return False

		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(password1, salt)
		if not self.db.insertUser(username, firstname, lastname, hash):
			return False

		userId = self.db.getUserIdFromUserName(username)
		deviceId = self.db.getDeviceIdFromDeviceStr(deviceStr)
		self.db.updateDevice(deviceId, userId)
			
		return True

	def listUsersFollowedBy(username):
		return self.db.listUsersFollowedBy(username)

	def listUsersFollowing(username):
		return self.db.listUsersFollowing(username)

	def inviteToFollow(self, username, followedByName):
		if len(username) == 0:
			return False
		if len(followedByName) == 0:
			return False

		return self.db.insertToFollowedByList(username, followedByName)

	def requestToFollow(self, username, followingName):
		if len(username) == 0:
			return False
		if len(followingName) == 0:
			return False

		return self.db.insertToFollowingList(username, followedByName)

class ExertWeb(object):
	_cp_config = {
		'tools.sessions.on': True,
		'tools.auth.on': True
	}

	def __init__(self, mgr):
		self.mgr = mgr
		super(ExertWeb, self).__init__()

	def terminate(self):
		print "Terminating ExertWeb"
		self.mgr.terminate()
		self.mgr = None

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
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
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
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def liser_users_following(self, username=None, num=None, *args, **kw):
		if username is None:
			return ""
		
		try:
			followers = self.mgr.db.listUsersFollowing(username)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})
			
			response += "]"
			
			return response
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def liser_users_followed_by(self, username=None, num=None, *args, **kw):
		if username is None:
			return ""

		try:
			followers = self.mgr.db.listUsersFollowedBy(username)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})

			response += "]"
			
			return response
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	def renderPageForDeviceId(self, deviceStr, deviceId):
		if deviceStr is None or deviceId is None:
			myTemplate = Template(filename=g_errorLoggedInHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="There is no data for the specified user.")

		activityId = self.mgr.db.getLatestActivityIdForDevice(deviceId)
		locations = self.mgr.db.listLocations(deviceId, activityId)

		if locations is None or len(locations) == 0:
			myTemplate = Template(filename=g_errorLoggedInHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="There is no data for the specified user.")

		route = ""
		centerLat = 0
		centerLon = 0

		for location in locations:
			route += "\t\t\t\tnew google.maps.LatLng(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

		if len(locations) > 0:
			centerLat = locations[0].latitude
			centerLon = locations[0].longitude

		myTemplate = Template(filename=g_mapSingleHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(deviceStr=deviceStr, centerLat=centerLat, centerLon=centerLon, route=route, routeLen=len(locations), activityId=str(activityId))

	@cherrypy.expose
	def device(self, deviceStr=None, *args, **kw):
		try:
			deviceId = self.mgr.db.getDeviceIdFromDeviceStr(deviceStr)
			if deviceId is None:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to process request. Unknown device ID.")
			else:
				return self.renderPageForDeviceId(deviceStr, deviceId)
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	def user(self, username=None, *args, **kw):
		try:
			deviceId, deviceStr = self.mgr.db.getDeviceFromUsername(username)
			if deviceId is None:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to process request. Unknown device ID.")
			else:
				return self.renderPageForDeviceId(deviceId)
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""
	
	@cherrypy.expose
	@require()
	def show_followed_by(self, username=None, *args, **kw):
		try:
			list = ""

			followers = self.mgr.listUsersFollowedBy(username)
			for follower in followers:
				list += follower + "\n"
			
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="foo.")
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	@require()
	def show_following(self, username=None, *args, **kw):
		try:
			followers = self.mgr.listUsersFollowing(username)
			for follower in followers:
				list += follower + "\n"

			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="foo.")
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	@require()
	def invite_to_follow(self, username=None, target_username=None, *args, **kw):
		try:
			if self.mgr.inviteToFollow(username, target_username):
				return ""
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to process request.")
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	@require()
	def request_to_follow(self, username=None, target_username=None, *args, **kw):
		try:
			if self.mgr.requestToFollow(username, target_username):
				return ""
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to process request.")
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	def login_submit(self, username, password, *args, **kw):
		try:
			if self.mgr.authenticateUser(username, password):
				cherrypy.session.regenerate()
				cherrypy.session[SESSION_KEY] = cherrypy.request.login = username
				return self.show_following(username)
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to authenticate the user.")
		except:
			cherrypy.response.status = 500
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	def create_login_submit(self, username, firstname, lastname, password1, password2, *args, **kw):
		try:
			if self.mgr.createUser(username, firstname, lastname, password1, password2, ""):
				return self.show_following(username)
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				return myTemplate.render(root_url=g_rootUrl, error="Unable to create the user.")
		except:
			myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="Internal Error.")
		return ""

	@cherrypy.expose
	def login(self):
		myTemplate = Template(filename=g_loginHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	@cherrypy.expose
	def create_login(self):
		myTemplate = Template(filename=g_createLoginHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	@cherrypy.expose
	def about(self):
		myTemplate = Template(filename=g_aboutHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	@cherrypy.expose
	def index(self):
		return self.login()


debug = True

if debug:
	g_rootUrl = ""
else:
	Daemonizer(cherrypy.engine).subscribe()

signal.signal(signal.SIGINT, signal_handler)
mako.collection_size = 100
mako.directories = "templates"

mgr = DataMgr()
g_app = ExertWeb(mgr)

conf = {
	'/':
	{
		'tools.staticdir.root': g_rootDir
	},
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
					   'server.socket_host': '127.0.0.1',
					   'requests.show_tracebacks': False,
					   'log.access_file': g_accessLog,
					   'log.error_file': g_exertLog } )
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)
cherrypy.quickstart(g_app, config=conf)
