# Copyright 2017 Michael J Simms

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

import DataMgr
import UserMgr

from dateutil.tz import tzlocal
from cherrypy import tools
from cherrypy.process.plugins import Daemonizer
from mako.lookup import TemplateLookup
from mako.template import Template

g_root_dir                  = os.path.dirname(os.path.abspath(__file__))
g_root_url                  = 'http://straen-app.com/live'
g_access_log                = 'access.log'
g_error_log                 = 'error.log'
g_product_name              = 'Straen'
g_tempmod_dir               = os.path.join(g_root_dir, 'tempmod')
g_map_single_html_file      = os.path.join(g_root_dir, 'html', 'map_single.html')
g_error_html_file           = os.path.join(g_root_dir, 'html', 'error.html')
g_error_logged_in_html_file = os.path.join(g_root_dir, 'html', 'error_logged_in.html')
g_app                       = None

SESSION_KEY       = '_cp_username'

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

class StraenWeb(object):
	_cp_config = {
		'tools.sessions.on': True,
		'tools.auth.on': True
	}

	def __init__(self, user_mgr, data_mgr):
		self.user_mgr = user_mgr
		self.data_mgr = data_mgr
		super(StraenWeb, self).__init__()

	def terminate(self):
		print "Terminating"
		self.user_mgr.terminate()
		self.user_mgr = None
		self.data_mgr.terminate()
		self.data_mgr = None

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def update_track(self, device_str=None, activity_id_str=None, num=None, *args, **kw):
		if device_str is None:
			return ""
		if activity_id_str is None:
			return ""
		if num is None:
			return ""
		
		try:
			activity_id = int(activity_id_str)
			if activity_id == 0:
				return ""

			locations = self.data_mgr.retrieve_most_recent_locations(device_str, activity_id, int(num))

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
	def update_metadata(self, device_str=None, activity_id_str=None, *args, **kw):
		if device_str is None:
			return ""
		if activity_id_str is None:
			return ""

		try:
			activity_id = int(activity_id_str)
			if activity_id == 0:
				return ""

			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["

			names = self.data_mgr.retrieve_metadata(NAME_KEY, device_str, activity_id)
			if names != None and len(names) > 0:
				response += json.dumps({"name":NAME_KEY, "value":names[-1][1]})

			times = self.data_mgr.retrieve_metadata(TIME_KEY, device_str, activity_id)
			if times != None and len(times) > 0:
				if len(response) > 1:
					response += ","
				localtimezone = tzlocal()
				valueStr = datetime.datetime.fromtimestamp(times[-1][1] / 1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
				response += json.dumps({"name":TIME_KEY, "value":valueStr})

			distances = self.data_mgr.retrieve_metadata(DISTANCE_KEY, device_str, activity_id)
			if distances != None and len(distances) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":DISTANCE_KEY, "value":"{:.2f}".format(distances[-1][1])})

			avg_speeds = self.data_mgr.retrieve_metadata(AVG_SPEED_KEY, device_str, activity_id)
			if avg_speeds != None and len(avg_speeds) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":AVG_SPEED_KEY, "value":"{:.2f}".format(avg_speeds[-1][1])})

			moving_speeds = self.data_mgr.retrieve_metadata(MOVING_SPEED_KEY, device_str, activity_id)
			if moving_speeds != None and len(moving_speeds) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":MOVING_SPEED_KEY, "value":"{:.2f}".format(moving_speeds[-1][1])})

			heart_rates = self.data_mgr.retrieve_sensordata(HEART_RATE_DB_KEY, device_str, activity_id)
			if heart_rates != None and len(heart_rates) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":HEART_RATE_KEY, "value":"{:.2f} bpm".format(heart_rates[-1][1])})

			cadences = self.data_mgr.retrieve_sensordata(CADENCE_DB_KEY, device_str, activity_id)
			if cadences != None and len(cadences) > 0:
				if len(response) > 1:
					response += ","
				response += json.dumps({"name":CADENCE_KEY, "value":"{:.2f}".format(distances[-1][1])})

			powers = self.data_mgr.retrieve_sensordata(POWER_DB_KEY, device_str, activity_id)
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
	def list_users_following(self, email=None, *args, **kw):
		if email is None:
			return ""
		
		try:
			followers = self.user_mgr.list_users_following(email)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})
			
			response += "]"
			
			return response
		except:
			cherrypy.log.error('Unhandled exception in list_users_following', 'EXEC', logging.WARNING)

		return ""

	@cherrypy.tools.json_out()
	@cherrypy.expose
	def list_users_followed_by(self, email=None, *args, **kw):
		if email is None:
			return ""

		try:
			followers = self.user_mgr.retrieve_users_followed_by(email)
			
			cherrypy.response.headers['Content-Type'] = 'application/json'
			response = "["
			
			for follower in followers:
				if len(response) > 1:
					response += ","
				response += json.dumps({"username":follower})

			response += "]"
			
			return response
		except:
			cherrypy.log.error('Unhandled exception in list_users_followed_by', 'EXEC', logging.WARNING)

		return ""
		
	# Helper function for building the navigation bar.
	def create_navbar(self, email):
		str = "<nav>\n" \
			"\t<ul>\n" \
			"\t\t<li><a href=\"" + g_root_url + "/my_activities/" + email + "\">My Activities</a></li>\n" \
			"\t\t<li><a href=\"" + g_root_url + "/all_activities/" + email + "\">All Activities</a></li>\n" \
			"\t\t<li><a href=\"" + g_root_url + "/following/" + email + "\">Following</a></li>\n" \
			"\t\t<li><a href=\"" + g_root_url + "/followers/" + email + "\">Followers</a></li>\n" \
			"\t\t<li><a href=\"" + g_root_url + "/device_list/" + email + "\">Devices</a></li>\n" \
			"\t</ul>\n" \
			"</nav>"
		return str

	# Helper function for rendering the map corresonding to a specific device and activity.
	def render_page_for_activity(self, email, user_realname, device_str, activity_id):
		if device_str is None:
			my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
			return my_template.render(product=g_product_name, root_url=g_root_url, error="There is no data for the specified device.")

		locations = self.data_mgr.retrieve_locations(device_str, activity_id)
		if locations is None or len(locations) == 0:
			my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
			return my_template.render(product=g_product_name, root_url=g_root_url, error="There is no data for the specified device.")

		route = ""
		center_lat = 0
		center_lon = 0
		last_lat = 0
		last_lon = 0

		for location in locations:
			route += "\t\t\t\tnewCoord(" + str(location['latitude']) + ", " + str(location['longitude']) + "),\n"
			lastLoc = location

		if len(locations) > 0:
			first_loc = locations[0]
			center_lat = first_loc['latitude']
			center_lon = first_loc['longitude']
			last_lat = lastLoc['latitude']
			last_lon = lastLoc['longitude']

		current_speeds = self.data_mgr.retrieve_metadata(CURRENT_SPEED_KEY, device_str, activity_id)
		current_speeds_str = ""
		if current_speeds is not None and isinstance(current_speeds, list):
			for value in current_speeds:
				current_speeds_str += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		heart_rates = self.data_mgr.retrieve_sensordata(HEART_RATE_DB_KEY, device_str, activity_id)
		heart_rates_str = ""
		if heart_rates is not None and isinstance(heart_rates, list):
			for value in heart_rates:
				heart_rates_str += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		cadences = self.data_mgr.retrieve_sensordata(CADENCE_DB_KEY, device_str, activity_id)
		cadences_str = ""
		if cadences is not None and isinstance(cadences, list):
			for value in cadences:
				cadences_str += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		powers = self.data_mgr.retrieve_sensordata(POWER_DB_KEY, device_str, activity_id)
		powers_str = ""
		if powers is not None and isinstance(powers, list):
			for value in powers:
				powers_str += "\t\t\t\t{ date: new Date(" + str(value[0]) + "), value: " + str(value[1]) + " },\n"

		my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
		return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, deviceStr=device_str, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=str(activity_id), currentSpeeds=current_speeds_str, heartRates=heart_rates_str, powers=powers_str)

	# Helper function for rendering the map corresonding to a multiple devices.
	def render_page_for_multiple_devices(self, email, user_realname, device_strs, user_id):
		if device_strs is None:
			my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
			return my_template.render(product=g_product_name, root_url=g_root_url, error="No device IDs were specified.")

		route_coordinates = ""
		center_lat = 0
		center_lon = 0
		last_lat = 0
		last_lon = 0
		device_index = 0

		for device_str in device_strs:
			activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
			if activity_id is None:
				continue
			locations = self.data_mgr.retrieve_locations(device_str, activity_id)
			if locations is None:
				continue
		
			route_coordinates += "\t\t\tvar routeCoordinates" + str(device_index) + " = \n\t\t\t[\n"
			for location in locations:
				route_coordinates += "\t\t\t\tnewCoord(" + str(location['latitude']) + ", " + str(location[']longitude']) + "),\n"
				lastLoc = location
			route_coordinates += "\t\t\t];\n"
			route_coordinates += "\t\t\taddRoute(routeCoordinates" + str(device_index) + ");\n\n"

			if len(locations) > 0:
				first_loc = locations[0]
				center_lat = first_loc['latitude']
				center_lon = first_loc['longitude']
				last_lat = lastLoc['latitude']
				last_lon = lastLoc['longitude']
		
		my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
		return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, center_lat=center_lat, center_lon=center_lon, last_lat=last_lat, last_lon=last_lon, route_coordinates=route_coordinates, routeLen=len(locations), user_id=str(user_id))
		
	# Helper function for creating a table row describing an activity
	def render_activity_row(self, user_realname, activity):
		row  = "<tr>"
		row += "<td>"
		if 'activity_id' in activity:
			row += activity['activity_id']
		else:
			row += ""
		row += "</td>"
		row += "<td>"
		if user_realname is not None:
			row += user_realname
			row += "<br>"
		row += "<a href=\"" + g_root_url + "\\device\\" + activity['device_str'] + "?activity_id=" + activity['activity_id'] + "\">"
		if 'activity_name' in activity:
			row += activity['activity_name']
		else:
			row += "Untitled"
		row += "</a></td>"
		row += "<td>"
		row += "<input type=\"checkbox\" name=\"public\" value=\"\" checked>"
		row += "</td>"
		row += "</tr>\n"
		return row
		
	# Helper function for creating a table row describing a user
	def render_user_row(self, user):
		row  = "<tr>"
		row += "<td>"
		row += user
		row += "</td>"
		row += "</tr>\n"
		return row

	# Renders the errorpage.
	@cherrypy.expose
	def error(self, str=None):
		try:
			cherrypy.response.status = 500
			my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
			if str is None:
				str = "Internal Error."
		except:
			pass
		return my_template.render(product=g_product_name, root_url=g_root_url, error=str)

	# Renders the map page for a single device.
	@cherrypy.expose
	def device(self, device_str, *args, **kw):
		try:
			activity_id_str = cherrypy.request.params.get("activity_id")
			if activity_id_str is None:
				activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
			else:
				activity_id = int(activity_id_str)

			if activity_id is None:
				return self.error()
			result = self.render_page_for_activity("", "", device_str, activity_id)
			return result
		except:
			cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of the specified user's activities.
	@cherrypy.expose
	def my_activities(self, email, *args, **kw):
		try:
			user_id, user_hash, user_realname = self.user_mgr.retrieve_user(email)
			activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
			activities_list_str = ""
			if activities is not None and isinstance(activities, list):
				for activity in activities:
					activities_list_str += self.render_activity_row(user_realname, activity)
			html_file = os.path.join(g_root_dir, 'html', 'my_activities.html')
			my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
			return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, activities_list=activities_list_str)
		except:
			cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of all activities the specified user is allowed to view.
	@cherrypy.expose
	def all_activities(self, email, *args, **kw):
		try:
			user_id, user_hash, user_realname = self.user_mgr.retrieve_user(email)
			activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
			activities_list_str = ""
			if activities is not None and isinstance(activities, list):
				for activity in activities:
					activities_list_str += self.render_activity_row(None, activity)
			html_file = os.path.join(g_root_dir, 'html', 'all_activities.html')
			my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
			return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, activities_list=activities_list_str)
		except:
			cherrypy.log.error('Unhandled exception in all_activities', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of users the specified user is following.
	@cherrypy.expose
	def following(self, email, *args, **kw):
		try:
			user_id, user_hash, user_realname = self.user_mgr.retrieve_user(email)
			users_following = self.user_mgr.list_users_following(user_id)
			users_list_str = ""
			if users_following is not None and isinstance(users_following, list):
				for user in users_following:
					users_list_str += self.render_user_row(user)
			html_file = os.path.join(g_root_dir, 'html', 'following.html')
			my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
			return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, users_list=users_list_str)
		except:
			cherrypy.log.error('Unhandled exception in following', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of users that are following the specified user.
	@cherrypy.expose
	def followers(self, email, *args, **kw):
		try:
			user_id, user_hash, user_realname = self.user_mgr.retrieve_user(email)
			users_followed_by = self.user_mgr.list_users_followed_by(user_id)
			users_list_str = ""
			if users_followed_by is not None and isinstance(users_followed_by, list):
				for user in users_followed_by:
					users_list_str += self.render_user_row(user)
			html_file = os.path.join(g_root_dir, 'html', 'followers.html')
			my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
			return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, users_list=users_list_str)
		except:
			cherrypy.log.error('Unhandled exception in followed_by', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the list of a user's devices.
	@cherrypy.expose
	def device_list(self, email, *args, **kw):
		try:
			user_id, user_hash, user_realname = self.user_mgr.retrieve_user(email)
			devices = self.user_mgr.list_user_devices(user_id)
			device_list_str = ""
			if devices is not None and isinstance(devices, list):
				for device in devices:
					device_list_str += "<tr>"
					device_list_str += "<td>"
					device_list_str += device
					device_list_str += "\n"
					device_list_str += "</td>"
					device_list_str += "</tr>\n"
			html_file = os.path.join(g_root_dir, 'html', 'device_list.html')
			my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
			return my_template.render(nav=self.create_navbar(email), product=g_product_name, root_url=g_root_url, email=email, name=user_realname, device_list=device_list_str)
		except:
			cherrypy.log.error('Unhandled exception in device_list', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the page for inviting someone to follow.
	@cherrypy.expose
	@require()
	def request_to_follow(self, email, target_email, *args, **kw):
		try:
			if self.user_mgr.request_to_follow(email, target_email):
				result = ""
			else:
				my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
				result = my_template.render(product=g_product_name, root_url=g_root_url, error="Unable to process the request.")
			return result
		except:
			cherrypy.log.error('Unhandled exception in request_to_follow', 'EXEC', logging.WARNING)
		return self.error()

	# Processes a login.
	@cherrypy.expose
	def submit_login(self, *args, **kw):
		try:
			email = cherrypy.request.params.get("email")
			password = cherrypy.request.params.get("password")

			if email is None or password is None:
				my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
				result = my_template.render(product=g_product_name, root_url=g_root_url, error="An email address and password were not provided.")
			else:
				user_logged_in, info_str = self.user_mgr.authenticate_user(email, password)
				if user_logged_in:
					cherrypy.session.regenerate()
					cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
					result = self.all_activities(email, None, None)
				else:
					my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
					error_msg = "Unable to authenticate the user."
					if len(info_str) > 0:
						error_msg += " "
						error_msg += info_str
					result = my_template.render(product=g_product_name, root_url=g_root_url, error=error_msg)
			return result
		except:
			cherrypy.log.error('Unhandled exception in submit_login', 'EXEC', logging.WARNING)
		return self.error()

	# Creates a new login.
	@cherrypy.expose
	def submit_new_login(self, email, realname, password1, password2, *args, **kw):
		try:
			user_created, info_str = self.user_mgr.create_user(email, realname, password1, password2, "")
			if user_created:
				cherrypy.session.regenerate()
				cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
				result = self.all_activities(email, *args, **kw)
			else:
				my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
				error_msg = "Unable to create the user."
				if len(info_str) > 0:
					error_msg += " "
					error_msg += info_str
				result = my_template.render(product=g_product_name, root_url=g_root_url, error=error_msg)
			return result
		except:
			cherrypy.log.error('Unhandled exception in submit_new_login', 'EXEC', logging.WARNING)
		return self.error()

	# Renders the login page.
	@cherrypy.expose
	def login(self):
		try:
			login_html_file = os.path.join(g_root_dir, 'html', 'login.html')
			my_template = Template(filename=login_html_file, module_directory=g_tempmod_dir)
			result = my_template.render(product=g_product_name, root_url=g_root_url)
		except:
			result = self.error()
		return result

	# Renders the create login page.
	@cherrypy.expose
	def create_login(self):
		try:
			create_login_html_file = os.path.join(g_root_dir, 'html', 'create_login.html')
			my_template = Template(filename=create_login_html_file, module_directory=g_tempmod_dir)
			result = my_template.render(product=g_product_name, root_url=g_root_url)
		except:
			result = self.error()
		return result

	# Renders the about page.
	@cherrypy.expose
	def about(self):
		try:
			about_html_file = os.path.join(g_root_dir, 'html', 'about.html')
			my_template = Template(filename=about_html_file, module_directory=g_tempmod_dir)
			result = my_template.render(product=g_product_name, root_url=g_root_url)
		except:
			result = self.error()
		return result

	# Renders the index page.
	@cherrypy.expose
	def index(self):
		return self.login()


debug = False

for arg in sys.argv:
	if arg == 'debug' or arg == '--debug':
		debug = True

if debug:
	g_root_url = ""
else:
	Daemonizer(cherrypy.engine).subscribe()

signal.signal(signal.SIGINT, signal_handler)
mako.collection_size = 100
mako.directories = "templates"

user_mgr = UserMgr.UserMgr(g_root_dir)
data_mgr = DataMgr.DataMgr(g_root_dir)
g_app = StraenWeb(user_mgr, data_mgr)

conf = {
	'/':
	{
		'tools.staticdir.root': g_root_dir
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
					   'log.access_file': g_access_log,
					   'log.error_file': g_error_log } )
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)
cherrypy.quickstart(g_app, config=conf)
