import cherrypy
import datetime
import json
import logging
import mako
import os
import re
import signal
import sys
import traceback
import bcrypt
import StraenDb

from random import randint
from dateutil.tz import tzlocal
from cherrypy import tools
from cherrypy.process.plugins import Daemonizer
from mako.lookup import TemplateLookup
from mako.template import Template

g_rootDir               = os.path.dirname(os.path.abspath(__file__))
g_rootUrl               = 'http://straen-app.com/live'
g_accessLog             = 'access.log'
g_errorLog              = 'error.log'
g_tempmodDir            = os.path.join(g_rootDir, 'tempmod')
g_loginHtmlFile         = os.path.join(g_rootDir, 'login.html')
g_createLoginHtmlFile   = os.path.join(g_rootDir, 'create_login.html')
g_mapSingleHtmlFile     = os.path.join(g_rootDir, 'map_single.html')
g_errorHtmlFile         = os.path.join(g_rootDir, 'error.html')
g_errorLoggedInHtmlFile = os.path.join(g_rootDir, 'error_logged_in.html')
g_userHtmlFile          = os.path.join(g_rootDir, 'user.html')
g_aboutHtmlFile         = os.path.join(g_rootDir, 'about.html')
g_app                   = None

SESSION_KEY       = '_cp_username'
MIN_PASSWORD_LEN  = 8

NAME_KEY          = "Name"
TIME_KEY          = "Time"
DISTANCE_KEY      = "Distance"
CADENCE_KEY       = "Cadence"
CURRENT_SPEED_KEY = "Current Speed"
AVG_SPEED_KEY     = "Avg. Speed"
MOVING_SPEED_KEY  = "Moving Speed"
HEART_RATE_KEY    = "Heart Rate"
POWER_KEY         = "Power"

CADENCE_DB_KEY    = 1
HEART_RATE_DB_KEY = 2
POWER_DB_KEY      = 3

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
		self.db = StraenDb.StraenDb(g_rootDir)
		super(DataMgr, self).__init__()

	def terminate(self):
		self.db = None

	def authenticate_user(self, email, password):
		if len(email) == 0:
			return False, "An email address was not provided."
		if len(password) < MIN_PASSWORD_LEN:
			return False, ""

		dbHash = self.db.retrieve_user_hash(email)
		if dbHash == 0:
			return False, "The user could not be found."
		if dbHash == bcrypt.hashpw(password, dbHash):
			loggedIn = True
			authStr = "The user has been logged in."
		else:
			loggedIn = False
			authStr = "The password is invalid."
		return loggedIn, authStr

	def create_user(self, email, realname, password1, password2, deviceStr):
		if len(email) == 0:
			return False, "Email address not provided."
		if len(realname) == 0:
			return False, "Name not provided."
		if len(password1) < MIN_PASSWORD_LEN:
			return False, "The password is too short."
		if password1 != password2:
			return False, "The passwords do not match."
		if self.db.retrieve_user_hash(email) != 0:
			return False, "The user already exists."

		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(password1, salt)
		if not self.db.create_user(email, realname, hash):
			return False, ""

		userId = self.db.retrieve_user_id_from_username(email)

		if len(deviceStr) > 0:
			deviceId = self.db.retrieve_device_id_from_device_str(deviceStr)
			self.db.update_device(deviceId, userId)
		
		return True, "The user was created."

	def list_users_followed_by(self, email):
		return self.db.retrieve_users_followed_by(email)

	def list_users_following(self, email):
		return self.db.retrieve_users_following(email)

	def invite_to_follow(self, email, followedByName):
		if len(email) == 0:
			return False
		if len(followedByName) == 0:
			return False

		return self.db.create_followed_by_entry(email, followedByName)

	def request_to_follow(self, email, followingName):
		if len(email) == 0:
			return False
		if len(followingName) == 0:
			return False

		return self.db.create_following_entry(email, followedByName)

class StraenWeb(object):
	_cp_config = {
		'tools.sessions.on': True,
		'tools.auth.on': True
	}

	def __init__(self, mgr):
		self.mgr = mgr
		super(StraenWeb, self).__init__()

	def terminate(self):
		print "Terminating"
		self.mgr.terminate()
		self.mgr = None

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def update_track(self, deviceStr=None, activityIdStr=None, num=None, *args, **kw):
		if deviceStr is None:
			return ""
		if activityIdStr is None:
			return ""
		if num is None:
			return ""
		
		try:
			deviceId = self.mgr.db.retrieve_device_id_from_device_str(deviceStr)
			activityId = int(activityIdStr)
			if activityId == 0:
				return ""

			locations = self.mgr.db.retrieve_most_recent_locations(deviceId, activityId, int(num))

			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["

			for location in locations:
				if len(response) > 1:
					response += ","
				response += json.dumps({"latitude":location.latitude, "longitude":location.longitude})

			response += "]"

			return response
		except:
			pass

		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def update_metadata(self, deviceStr=None, activityIdStr=None, *args, **kw):
		if deviceStr is None:
			return ""
		if activityIdStr is None:
			return ""

		try:
			deviceId = self.mgr.db.retrieve_device_id_from_device_str(deviceStr)
			activityId = int(activityIdStr)
			if activityId == 0:
				return ""

			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			names = self.mgr.db.retrieve_metadata(NAME_KEY, deviceId, activityId)
			if names != None and len(names) > 0:
				response += json.dumps({"name":NAME_KEY, "value":names[-1][1]})

			times = self.mgr.db.retrieve_metadata(TIME_KEY, deviceId, activityId)
			if times != None and len(times) > 0:
				if len(response) > 1:
					response += ","
				localtimezone = tzlocal()
				valueStr = datetime.datetime.fromtimestamp(times[-1][1] / 1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
				response += json.dumps({"name":TIME_KEY, "value":valueStr})

			distances = self.mgr.db.retrieve_metadata(DISTANCE_KEY, deviceId, activityId)
			if distances != None and len(distances) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":DISTANCE_KEY, "value":"{:.2f}".format(distances[-1][1])})

			avgSpeeds = self.mgr.db.retrieve_metadata(AVG_SPEED_KEY, deviceId, activityId)
			if avgSpeeds != None and len(avgSpeeds) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":AVG_SPEED_KEY, "value":"{:.2f}".format(avgSpeeds[-1][1])})

			movingSpeeds = self.mgr.db.retrieve_metadata(MOVING_SPEED_KEY, deviceId, activityId)
			if movingSpeeds != None and len(movingSpeeds) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":MOVING_SPEED_KEY, "value":"{:.2f}".format(movingSpeeds[-1][1])})

			heartRates = self.mgr.db.retrieve_sensordata(HEART_RATE_DB_KEY, deviceId, activityId)
			if heartRates != None and len(heartRates) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":HEART_RATE_KEY, "value":"{:.2f} bpm".format(heartRates[-1][1])})

			cadences = self.mgr.db.retrieve_sensordata(CADENCE_DB_KEY, deviceId, activityId)
			if cadences != None and len(cadences) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":CADENCE_KEY, "value":"{:.2f}".format(distances[-1][1])})
			
			powers = self.mgr.db.retrieve_sensordata(POWER_DB_KEY, deviceId, activityId)
			if powers != None and len(powers) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":POWER_KEY, "value":"{:.2f} watts".format(powers[-1][1])})

			response += "]"

			return response
		except:
			cherrypy.log.error('Unhandled exception in update_metadata', 'EXEC', logging.WARNING)

		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def liser_users_following(self, email=None, *args, **kw):
		if email is None:
			return ""
		
		try:
			followers = self.mgr.list_users_following(email)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})
			
			response += "]"
			
			return response
		except:
			cherrypy.log.error('Unhandled exception in liser_users_following', 'EXEC', logging.WARNING)

		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def liser_users_followed_by(self, email=None, *args, **kw):
		if email is None:
			return ""

		try:
			followers = self.mgr.retrieve_users_followed_by(email)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})

			response += "]"
			
			return response
		except:
			cherrypy.log.error('Unhandled exception in liser_users_followed_by', 'EXEC', logging.WARNING)

		return ""

	# Helper function for rendering the map corresonding to a specific device and activity.
	def render_page_for_activity(self, deviceStr, deviceId, activityId):
		if deviceStr is None or deviceId is None:
			myTemplate = Template(filename=g_errorLoggedInHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="There is no data for the specified device.")

		locations = self.mgr.db.retrieve_locations(deviceId, activityId)
		if locations is None or len(locations) == 0:
			myTemplate = Template(filename=g_errorLoggedInHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="There is no data for the specified device.")

		route = ""
		centerLat = 0
		centerLon = 0
		lastLat = 0
		lastLon = 0

		for location in locations:
			route += "\t\t\t\tnewCoord(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"

		if len(locations) > 0:
			centerLat = locations[0].latitude
			centerLon = locations[0].longitude
			lastLat = locations[len(locations) - 1].latitude
			lastLon = locations[len(locations) - 1].longitude

		currentSpeeds = self.mgr.db.retrieve_metadata(CURRENT_SPEED_KEY, deviceId, activityId)
		currentSpeedsStr = ""
		for value in currentSpeeds:
			currentSpeedsStr += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		heartRates = self.mgr.db.retrieve_sensordata(HEART_RATE_DB_KEY, deviceId, activityId)
		heartRatesStr = ""
		for value in heartRates:
			heartRatesStr += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		cadences = self.mgr.db.retrieve_sensordata(CADENCE_DB_KEY, deviceId, activityId)
		cadencesStr = ""
		for value in cadences:
			cadencesStr += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		powers = self.mgr.db.retrieve_sensordata(POWER_DB_KEY, deviceId, activityId)
		powersStr = ""
		for value in powers:
			powersStr += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		myTemplate = Template(filename=g_mapSingleHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl, deviceStr=deviceStr, centerLat=centerLat, lastLat=lastLat, lastLon=lastLon, centerLon=centerLon, route=route, routeLen=len(locations), activityId=str(activityId), current_speeds=currentSpeedsStr, heart_rates=heartRatesStr, powers=powersStr)

	# Helper function for rendering the map corresonding to a multiple devices.
	def render_page_for_multiple_device_ids(self, deviceIds, userId):
		if deviceIds is None:
			myTemplate = Template(filename=g_errorLoggedInHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, error="No device IDs were specified.")

		routeCoordinates = ""
		centerLat = 0
		centerLon = 0
		lastLat = 0
		lastLon = 0
		deviceIndex = 0

		for deviceId in deviceIds:
			activityId = self.mgr.db.retrieve_most_recent_activity_id_for_device(deviceId)
			locations = self.mgr.db.retrieve_locations(deviceId, activityId)
		
			routeCoordinates += "\t\t\tvar routeCoordinates" + str(deviceIndex) + " = \n\t\t\t[\n"
			for location in locations:
				routeCoordinates += "\t\t\t\tnewCoord(" + str(location.latitude) + ", " + str(location.longitude) + "),\n"
			routeCoordinates += "\t\t\t];\n"
			routeCoordinates += "\t\t\taddRoute(routeCoordinates" + str(deviceIndex) + ");\n\n"

			if len(locations) > 0:
				centerLat = locations[0].latitude
				centerLon = locations[0].longitude
				lastLat = locations[len(locations) - 1].latitude
				lastLon = locations[len(locations) - 1].longitude
		
		myTemplate = Template(filename=g_mapSingleHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl, centerLat=centerLat, centerLon=centerLon, lastLat=lastLat, lastLon=lastLon, routeCoordinates=routeCoordinates, routeLen=len(locations), userId=str(userId))

	# Renders the errorpage.
	@cherrypy.expose
	def error(self, str=None):
		cherrypy.response.status = 500
		myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
		if str is None:
			str = "Internal Error."
		return myTemplate.render(root_url=g_rootUrl, error=str)

	# Renders the map page for a single device.
	@cherrypy.expose
	def device(self, deviceStr, *args, **kw):
		try:
			deviceId = self.mgr.db.retrieve_device_id_from_device_str(deviceStr)
			if deviceId is None:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				result = myTemplate.render(root_url=g_rootUrl, error="Unable to process the request. Unknown device ID.")
			else:
				activityIdStr = cherrypy.request.params.get("activityId")
				if activityIdStr is None:
					activityId = self.mgr.db.retrieve_most_recent_activity_id_for_device(deviceId)
				else:
					activityId = int(activityIdStr)
				result = self.render_page_for_activity(deviceStr, deviceId, activityId)
			return result
		except:
			cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of the specified user's activities.
	@cherrypy.expose
	def my_activities(self, email, *args, **kw):
		try:
			userId = self.mgr.db.retrieve_user_id_from_username(email)
		except:
			cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of all activities the specified user is allowed to view.
	@cherrypy.expose
	def all_activities(self, email, *args, **kw):
		try:
			userId = self.mgr.db.retrieve_user_id_from_username(email)
		except:
			cherrypy.log.error('Unhandled exception in all_activities', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of users the specified user is following.
	@cherrypy.expose
	def following(self, email, *args, **kw):
		try:
			userId = self.mgr.db.retrieve_user_id_from_username(email)
		except:
			cherrypy.log.error('Unhandled exception in following', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of users that are following the specified user.
	@cherrypy.expose
	def followed_by(self, email, *args, **kw):
		try:
			userId = self.mgr.db.retrieve_user_id_from_username(email)
		except:
			cherrypy.log.error('Unhandled exception in followed_by', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of a user's devices.
	@cherrypy.expose
	def device_list(self, email, *args, **kw):
		try:
			userId = self.mgr.db.retrieve_user_id_from_username(email)
			realname = self.mgr.db.retrieve_realname_from_username(email)
		except:
			cherrypy.log.error('Unhandled exception in device_list', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the dashboard page for an individual user.
	@cherrypy.expose
	def user(self, email, *args, **kw):
		try:
			realname = self.mgr.db.retrieve_realname_from_username(email)
			myTemplate = Template(filename=g_userHtmlFile, module_directory=g_tempmodDir)
			return myTemplate.render(root_url=g_rootUrl, email=email, name=realname, error="Internal Error.")
		except:
			cherrypy.log.error('Unhandled exception in user', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the page for inviting a follower
	@cherrypy.expose
	@require()
	def invite_to_follow(self, email, target_email, *args, **kw):
		try:
			if self.mgr.invite_to_follow(email, target_email):
				result = ""
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				result = myTemplate.render(root_url=g_rootUrl, error="Unable to process the request.")
			return result
		except:
			cherrypy.log.error('Unhandled exception in invite_to_follow', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the page for inviting someone to follow
	@cherrypy.expose
	@require()
	def request_to_follow(self, email, target_email, *args, **kw):
		try:
			if self.mgr.request_to_follow(email, target_email):
				result = ""
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				result = myTemplate.render(root_url=g_rootUrl, error="Unable to process the request.")
			return result
		except:
			cherrypy.log.error('Unhandled exception in request_to_follow', 'EXEC', logging.WARNING)
		return self.error()

	# Processes a login
	@cherrypy.expose
	def submit_login(self, *args, **kw):
		try:
			email = cherrypy.request.params.get("email")
			password = cherrypy.request.params.get("password")
			if email is None or password is None:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				result = myTemplate.render(root_url=g_rootUrl, error="An email address and password were not provided")
			else:
				userLoggedIn, infoStr = self.mgr.authenticate_user(email, password)
				if userLoggedIn:
					cherrypy.session.regenerate()
					cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
					result = self.user(email, None, None)
				else:
					myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
					errorMsg = "Unable to authenticate the user."
					if len(infoStr) > 0:
						errorMsg += " "
						errorMsg += infoStr
					result = myTemplate.render(root_url=g_rootUrl, error=errorMsg)
			return result
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
		return self.error()

	# Creates a new login
	@cherrypy.expose
	def submit_new_login(self, email, realname, password1, password2, *args, **kw):
		try:
			userCreated, infoStr = self.mgr.create_user(email, realname, password1, password2, "")
			if userCreated:
				cherrypy.session.regenerate()
				cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
				result = self.user(email, *args, **kw)
			else:
				myTemplate = Template(filename=g_errorHtmlFile, module_directory=g_tempmodDir)
				errorMsg = "Unable to create the user."
				if len(infoStr) > 0:
					errorMsg += " "
					errorMsg += infoStr
				result = myTemplate.render(root_url=g_rootUrl, error=errorMsg)
			return result
		except:
			cherrypy.log.error('Unhandled exception in submit_new_login', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the login page.
	@cherrypy.expose
	def login(self):
		myTemplate = Template(filename=g_loginHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	# Renders the create login page.
	@cherrypy.expose
	def create_login(self):
		myTemplate = Template(filename=g_createLoginHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	# Renders the about page.
	@cherrypy.expose
	def about(self):
		myTemplate = Template(filename=g_aboutHtmlFile, module_directory=g_tempmodDir)
		return myTemplate.render(root_url=g_rootUrl)

	# Renders the index page.
	@cherrypy.expose
	def index(self):
		return self.login()


debug = False

for arg in sys.argv:
	if arg == 'debug' or arg == '--debug':
		debug = True

if debug:
	g_rootUrl = ""
else:
	Daemonizer(cherrypy.engine).subscribe()

signal.signal(signal.SIGINT, signal_handler)
mako.collection_size = 100
mako.directories = "templates"

mgr = DataMgr()
g_app = StraenWeb(mgr)

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
					   'log.error_file': g_errorLog } )
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)
cherrypy.quickstart(g_app, config=conf)
