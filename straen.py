# Copyright 2017 Michael J Simms

import argparse
import cherrypy
import datetime
import gpxpy
import json
import logging
import mako
import os
import re
import signal
import shutil
import sys
import traceback
import uuid

import DataMgr
import UserMgr

from dateutil.tz import tzlocal
from cherrypy import tools
from cherrypy.process.plugins import Daemonizer
from mako.lookup import TemplateLookup
from mako.template import Template


ACCESS_LOG = 'access.log'
ERROR_LOG = 'error.log'
PRODUCT_NAME = 'Straen'
SESSION_KEY = '_straen_username'

g_root_dir = os.path.dirname(os.path.abspath(__file__))
g_root_url = 'http://straen-app.com'
g_tempfile_dir = os.path.join(g_root_dir, 'tempfile')
g_tempmod_dir = os.path.join(g_root_dir, 'tempmod')
g_map_single_html_file = os.path.join(g_root_dir, 'html', 'map_single.html')
g_error_html_file = os.path.join(g_root_dir, 'html', 'error.html')
g_error_logged_in_html_file = os.path.join(g_root_dir, 'html', 'error_logged_in.html')
g_app = None

NAME_KEY = "Name"
TIME_KEY = "Time"
DISTANCE_KEY = "Distance"
CADENCE_KEY = "Cadence"
CURRENT_SPEED_KEY = "Current Speed"
AVG_SPEED_KEY = "Avg. Speed"
MOVING_SPEED_KEY = "Moving Speed"
HEART_RATE_KEY = "Heart Rate"
POWER_KEY = "Power"


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
        requested_url = cherrypy.request.request_line.split()[1]
        requested_url_parts = requested_url.split('/')
        requested_url_parts = filter(lambda part: part != '', requested_url_parts)

        # If the user is trying to view an activity then make sure they have permissions
        # to view it. First check to see if it's a public activity.
        if requested_url_parts[0] == "device":
            url_params = requested_url_parts[1].split("?")
            if url_params is not None and len(url_params) >= 2:
                device = url_params[0]
                activity_params = url_params[1].split("=")
                if activity_params is not None and len(activity_params) >= 2:
                    activity_id = activity_params[1]
                    if g_app.activity_is_public(device, activity_id):
                        return

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
                response += json.dumps({"latitude": location.latitude, "longitude": location.longitude})

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
                response += json.dumps({"name": NAME_KEY, "value": names[-1][1]})

            times = self.data_mgr.retrieve_metadata(TIME_KEY, device_str, activity_id)
            if times != None and len(times) > 0:
                if len(response) > 1:
                    response += ","
                localtimezone = tzlocal()
                valueStr = datetime.datetime.fromtimestamp(times[-1][1] / 1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
                response += json.dumps({"name": TIME_KEY, "value": valueStr})

            distances = self.data_mgr.retrieve_metadata(DISTANCE_KEY, device_str, activity_id)
            if distances != None and len(distances) > 0:
                if len(response) > 1:
                    response += ","
                distance = distances[len(distances) - 1]
                value = float(distance.values()[0])
                response += json.dumps({"name": DISTANCE_KEY, "value": "{:.2f}".format(value)})

            avg_speeds = self.data_mgr.retrieve_metadata(AVG_SPEED_KEY, device_str, activity_id)
            if avg_speeds != None and len(avg_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = avg_speeds[len(avg_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": AVG_SPEED_KEY, "value": "{:.2f}".format(value)})

            moving_speeds = self.data_mgr.retrieve_metadata(MOVING_SPEED_KEY, device_str, activity_id)
            if moving_speeds != None and len(moving_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = moving_speeds[len(moving_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": MOVING_SPEED_KEY, "value": "{:.2f}".format(value)})

            heart_rates = self.data_mgr.retrieve_sensordata(HEART_RATE_KEY, device_str, activity_id)
            if heart_rates != None and len(heart_rates) > 0:
                if len(response) > 1:
                    response += ","
                heart_rate = heart_rates[len(heart_rates) - 1]
                value = float(heart_rate.values()[0])
                response += json.dumps({"name": HEART_RATE_KEY, "value": "{:.2f} bpm".format(value)})

            cadences = self.data_mgr.retrieve_sensordata(CADENCE_KEY, device_str, activity_id)
            if cadences != None and len(cadences) > 0:
                if len(response) > 1:
                    response += ","
                cadence = cadences[len(cadences) - 1]
                value = float(cadence.values()[0])
                response += json.dumps({"name": CADENCE_KEY, "value": "{:.2f}".format(value)})

            powers = self.data_mgr.retrieve_sensordata(POWER_KEY, device_str, activity_id)
            if powers != None and len(powers) > 0:
                if len(response) > 1:
                    response += ","
                power = powers[len(powers) - 1]
                value = float(power.values()[0])
                response += json.dumps({"name": POWER_KEY, "value": "{:.2f} watts".format(value)})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in update_metadata', 'EXEC', logging.WARNING)
        return ""

    # Login - called from the app.
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def login_submit(self, **kw):
        try:
            email = cherrypy.request.json["username"]
            password = cherrypy.request.json["password"]
            device_str = cherrypy.request.json["device"]

            response = "["

            if email is None or password is None:
                response += "\"error\": \"An email address and password were not provided.\""
            else:
                user_logged_in, info_str = self.user_mgr.authenticate_user(email, password)
                if user_logged_in:
                    self.user_mgr.create_user_device(email, device_str)
                else:
                    response += "\"error\": \"" + info_str + "\""

            response += "]"
            return response
        except:
            cherrypy.log.error('Unhandled exception in login_submit', 'EXEC', logging.WARNING)
        return ""

    # Creates a new login - called from the app.
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def create_login_submit(self, **kw):
        try:
            email = cherrypy.request.json["username"]
            password1 = cherrypy.request.json["password1"]
            password2 = cherrypy.request.json["password2"]
            realname = cherrypy.request.json["realname"]
            device_str = cherrypy.request.json["device"]

            response = "["
            user_created, info_str = self.user_mgr.create_user(email, realname, password1, password2, device_str)
            if user_created:
                response += "\"error\": \"" + info_str + "\""
            response += "]"
            return response
        except:
            cherrypy.log.error('Unhandled exception in create_login_submit', 'EXEC', logging.WARNING)
        return ""

    # Lists users followed by the logged in user - called from the app.
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def list_users_followed(self, email=None, *args, **kw):
        if email is None:
            return ""

        try:
            followers = self.user_mgr.list_users_followed(email)

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            for follower in followers:
                if len(response) > 1:
                    response += ","
                response += json.dumps({"username": follower})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in list_users_followed', 'EXEC', logging.WARNING)
        return ""

    # Lists users following the logged in user - called from the app.
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def list_followers(self, email=None, *args, **kw):
        if email is None:
            return ""

        try:
            followers = self.user_mgr.retrieve_followers(email)

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            for follower in followers:
                if len(response) > 1:
                    response += ","
                response += json.dumps({"username": follower})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in list_followers', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.expose
    def update_visibility(self, device_str, activity_id, visibility):
        if device_str is None:
            pass
        if activity_id is None:
            pass

        try:
            if visibility == "true" or visibility == "True":
                new_visibility = "public"
            else:
                new_visibility = "private"

            self.data_mgr.update_activity_visibility(device_str, int(activity_id), new_visibility)
        except:
            cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)

    # Helper function for building the navigation bar.
    @staticmethod
    def create_navbar(username):
        navbar_str = "<nav>\n" \
            "\t<ul>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/my_activities/\">My Activities</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/all_activities/\">All Activities</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/following/\">Following</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/followers/\">Followers</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/device_list/\">Devices</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/import_activity/\">Import</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/settings/\">Settings</a></li>\n" \
            "\t</ul>\n" \
            "</nav>"
        return navbar_str

    # Helper function for rendering the map corresonding to a specific device and activity.
    def render_page_for_activity(self, email, user_realname, device_str, activity_id):
        if device_str is None:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="There is no data for the specified device.")

        locations = self.data_mgr.retrieve_locations(device_str, activity_id)
        if locations is None or len(locations) == 0:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="There is no data for the specified device.")

        route = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0

        for location in locations:
            route += "\t\t\t\tnewCoord(" + str(location['latitude']) + ", " + str(location['longitude']) + "),\n"
            last_loc = location

        if len(locations) > 0:
            first_loc = locations[0]
            center_lat = first_loc['latitude']
            center_lon = first_loc['longitude']
            last_lat = last_loc['latitude']
            last_lon = last_loc['longitude']

        current_speeds = self.data_mgr.retrieve_metadata(CURRENT_SPEED_KEY, device_str, activity_id)
        current_speeds_str = ""
        if current_speeds is not None and isinstance(current_speeds, list):
            for current_speed in current_speeds:
                time = current_speed.keys()[0]
                value = current_speed.values()[0]
                current_speeds_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        heart_rates = self.data_mgr.retrieve_sensordata(HEART_RATE_KEY, device_str, activity_id)
        heart_rates_str = ""
        if heart_rates is not None and isinstance(heart_rates, list):
            for heart_rate in heart_rates:
                time = heart_rate.keys()[0]
                value = heart_rate.values()[0]
                heart_rates_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        cadences = self.data_mgr.retrieve_sensordata(CADENCE_KEY, device_str, activity_id)
        cadences_str = ""
        if cadences is not None and isinstance(cadences, list):
            for cadence in cadences:
                time = cadence.keys()[0]
                value = cadence.values()[0]
                cadences_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        powers = self.data_mgr.retrieve_sensordata(POWER_KEY, device_str, activity_id)
        powers_str = ""
        if powers is not None and isinstance(powers, list):
            for power in powers:
                time = power.keys()[0]
                value = power.values()[0]
                powers_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(email), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, deviceStr=device_str, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=str(activity_id), currentSpeeds=current_speeds_str, heartRates=heart_rates_str, powers=powers_str)

    # Helper function for rendering the map corresonding to a multiple devices.
    def render_page_for_multiple_devices(self, email, user_realname, device_strs, user_id):
        if device_strs is None:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="No device IDs were specified.")

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
                last_loc = location
            route_coordinates += "\t\t\t];\n"
            route_coordinates += "\t\t\taddRoute(routeCoordinates" + str(device_index) + ");\n\n"

            if len(locations) > 0:
                first_loc = locations[0]
                center_lat = first_loc['latitude']
                center_lon = first_loc['longitude']
                last_lat = last_loc['latitude']
                last_lon = last_loc['longitude']

        my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(email), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, center_lat=center_lat, center_lon=center_lon, last_lat=last_lat, last_lon=last_lon, route_coordinates=route_coordinates, routeLen=len(locations), user_id=str(user_id))

    # Helper function for creating a table row describing an activity.
    def render_activity_row(self, user_realname, activity, row_id):
        row = "<tr>"
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
        row += "<a href=\"" + g_root_url + "\\device\\" + \
            activity['device_str'] + "?activity_id=" + activity['activity_id'] + "\">"
        if 'activity_name' in activity:
            row += activity['activity_name']
        else:
            row += "Untitled"
        row += "</a></td>"
        row += "<td>"
        checkbox_value = "checked"
        checkbox_label = "Public"
        if 'visibility' in activity:
            if activity['visibility'] == "private":
                checkbox_value = "unchecked"
                checkbox_label = "Private"
        row += "<div>\n"
        row += "\t<input type=\"checkbox\" value=\"\" " + checkbox_value + " id=\"" + \
                    str(row_id) + "\" onclick='handleVisibilityClick(this, \"" + \
                    activity['device_str'] + "\", " + \
                    activity['activity_id'] + ")';>"
        row += "<span>" + checkbox_label + "</span></label>"
        row += "</div>\n"
        row += "</td>"
        row += "</tr>\n"
        return row

    # Helper function for creating a table row describing a user.
    @staticmethod
    def render_user_row(user):
        row = "<tr>"
        row += "<td>"
        row += user
        row += "</td>"
        row += "</tr>\n"
        return row

    # Returns TRUE if the logged in user is allowed to view the specified activity.
    def activity_is_public(self, device_str, activity_id):
        visibility = self.data_mgr.retrieve_activity_visibility(device_str, activity_id)
        if visibility is not None:
            if visibility == "public":
                return True
            elif visibility == "private":
                return False
        return True

    # Renders the errorpage.
    @cherrypy.expose
    def error(self, error_str=None):
        try:
            cherrypy.response.status = 500
            my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
            if error_str is None:
                error_str = "Internal Error."
        except:
            pass
        return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error=error_str)

    # Renders the map page for the current activity from a single device.
    @cherrypy.expose
    def live(self, device_str):
        try:
            activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id is None:
                return self.error()

            return self.render_page_for_activity("", "", device_str, activity_id)
        except:
            cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the map page for a single device.
    @cherrypy.expose
    @require()
    def device(self, device_str, *args, **kw):
        try:
            activity_id_str = cherrypy.request.params.get("activity_id")
            if activity_id_str is None:
                activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            else:
                activity_id = int(activity_id_str)

            if activity_id is None:
                return self.error()

            return self.render_page_for_activity("", "", device_str, activity_id)
        except:
            cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the list of the specified user's activities.
    @cherrypy.expose
    @require()
    def my_activities(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
            activities_list_str = ""
            row_id = 0
            if activities is not None and isinstance(activities, list):
                for activity in activities:
                    activities_list_str += self.render_activity_row(None, activity, row_id)
                    row_id = row_id + 1
            html_file = os.path.join(g_root_dir, 'html', 'my_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except:
            cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the list of all activities the specified user is allowed to view.
    @cherrypy.expose
    @require()
    def all_activities(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
            activities_list_str = ""
            row_id = 0
            if activities is not None and isinstance(activities, list):
                for activity in activities:
                    activities_list_str += self.render_activity_row(user_realname, activity, row_id)
                    row_id = row_id + 1
            html_file = os.path.join(g_root_dir, 'html', 'all_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except:
            cherrypy.log.error('Unhandled exception in all_activities', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the list of users the specified user is following.
    @cherrypy.expose
    @require()
    def following(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            users_following = self.user_mgr.list_users_followed(user_id)
            users_list_str = ""
            if users_following is not None and isinstance(users_following, list):
                for user in users_following:
                    users_list_str += self.render_user_row(user)
            html_file = os.path.join(g_root_dir, 'html', 'following.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except:
            cherrypy.log.error('Unhandled exception in following', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the list of users that are following the specified user.
    @cherrypy.expose
    @require()
    def followers(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            users_followed_by = self.user_mgr.list_followers(user_id)
            users_list_str = ""
            if users_followed_by is not None and isinstance(users_followed_by, list):
                for user in users_followed_by:
                    users_list_str += self.render_user_row(user)
            html_file = os.path.join(g_root_dir, 'html', 'followers.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except:
            cherrypy.log.error('Unhandled exception in followers', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the list of a user's devices.
    @cherrypy.expose
    @require()
    def device_list(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
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
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, device_list=device_list_str)
        except:
            cherrypy.log.error('Unhandled exception in device_list', 'EXEC', logging.WARNING)
        return self.error()

    def import_gpx_file(self, username, file_name):
        with open(file_name, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            lat = []
            lon = []

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        lat.append(point.latitude)
                        lon.append(point.longitude)

            print lat
            print lon

    def import_tcx_file(self, username, file_name):
        pass

    # Processes an upload request.
    @cherrypy.expose
    def upload(self, ufile):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            # Generate a random name for the local file.
            upload_path = os.path.normpath(g_tempfile_dir)
            uploaded_file_name, uploaded_file_ext = os.path.splitext(ufile.filename)
            local_file_name = os.path.join(upload_path, str(uuid.uuid4()))
            local_file_name = local_file_name + uploaded_file_ext

            # Write the file.
            with open(local_file_name, 'wb') as saved_file:
                while True:
                    data = ufile.file.read(8192)
                    if not data:
                        break
                    saved_file.write(data)

            # Parse the file.
            try:
                if uploaded_file_ext == '.gpx':
                    self.import_gpx_file(username, local_file_name)
                elif uploaded_file_ext == '.tcx':
                    self.import_gpx_file(username, local_file_name)
            except:
                cherrypy.log.error('Unhandled exception in upload when processing ' + uploaded_file_name, 'EXEC', logging.WARNING)

            # Remove the local file.
            os.remove(local_file_name)

        except:
            cherrypy.log.error('Unhandled exception in upload', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the import page.
    @cherrypy.expose
    @require()
    def import_activity(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            html_file = os.path.join(g_root_dir, 'html', 'import.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname)
        except:
            cherrypy.log.error('Unhandled exception in settings', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the user's settings page.
    @cherrypy.expose
    @require()
    def settings(self, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)
            html_file = os.path.join(g_root_dir, 'html', 'settings.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(username), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname)
        except:
            cherrypy.log.error('Unhandled exception in settings', 'EXEC', logging.WARNING)
        return self.error()

    # Renders the page for inviting someone to follow.
    @cherrypy.expose
    @require()
    def request_to_follow(self, email, target_email, *args, **kw):
        try:
            # Get the logged in user
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                return self.login()

            if self.user_mgr.request_to_follow(username, target_email):
                result = ""
            else:
                my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
                result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="Unable to process the request.")
            return result
        except:
            cherrypy.log.error('Unhandled exception in request_to_follow', 'EXEC', logging.WARNING)
        return self.error()

    # Processes a search user request.
    @cherrypy.expose
    @require()
    def submit_user_search(self, *args, **kw):
        try:
            user = cherrypy.request.params.get("searchname")
            matched_users = self.user_mgr.retrieve_matched_users(user)
            for matched_user in matched_users:
                pass
        except:
            cherrypy.log.error('Unhandled exception in submit_user_search', 'EXEC', logging.WARNING)
        return self.error()

    # Processes a login.
    @cherrypy.expose
    def submit_login(self, *args, **kw):
        try:
            email = cherrypy.request.params.get("email")
            password = cherrypy.request.params.get("password")

            if email is None or password is None:
                my_template = Template(filename=g_error_html_file, module_directory=g_tempmod_dir)
                result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="An email address and password were not provided.")
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
                    result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error=error_msg)
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
                result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error=error_msg)
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
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
        except:
            result = self.error()
        return result

    # Renders the create login page.
    @cherrypy.expose
    def create_login(self):
        try:
            create_login_html_file = os.path.join(g_root_dir, 'html', 'create_login.html')
            my_template = Template(filename=create_login_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
        except:
            result = self.error()
        return result

    # Renders the about page.
    @cherrypy.expose
    def about(self):
        try:
            about_html_file = os.path.join(g_root_dir, 'html', 'about.html')
            my_template = Template(filename=about_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
        except:
            result = self.error()
        return result

    # Renders the index page.
    @cherrypy.expose
    def index(self):
        return self.login()


# Parse command line options.
parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", default=False, help="Prevents the app from going into the background", required=False)
parser.add_argument("--port", type=int, default=8080, help="Port on which to listen", required=False)
parser.add_argument("--https", action="store_true", default=False, help="Runs the app as HTTPS", required=False)
parser.add_argument("--cert", default="cert.pem", help="Certificate file for HTTPS", required=False)
parser.add_argument("--privkey", default="privkey.pem", help="Private Key file for HTTPS", required=False)

try:
    args = parser.parse_args()
except IOError as e:
    parser.error(e)
    sys.exit(1)

if args.debug:
    if args.https:
        g_root_url = "https://127.0.0.1:" + str(args.port)
    else:
        g_root_url = "http://127.0.0.1:" + str(args.port)
else:
    if args.https:
        g_root_url = 'https://straen-app.com'
    else:
        g_root_url = 'http://straen-app.com'

    Daemonizer(cherrypy.engine).subscribe()

if args.https:
    print "Running HTTPS...."
    cherrypy.server.ssl_module = 'builtin'
    cherrypy.server.ssl_certificate = args.cert
    print "Certificate File: " + args.cert
    cherrypy.server.ssl_private_key = args.privkey
    print "Private Key File: " + args.privkey

signal.signal(signal.SIGINT, signal_handler)
mako.collection_size = 100
mako.directories = "templates"

if not os.path.exists(g_tempfile_dir):
    os.makedirs(g_tempfile_dir)

user_mgr = UserMgr.UserMgr(g_root_dir)
data_mgr = DataMgr.DataMgr(g_root_dir)
g_app = StraenWeb(user_mgr, data_mgr)

cherrypy.tools.my_auth = cherrypy.Tool('before_handler', check_auth)

conf = {
    '/':
    {
        'tools.staticdir.root': g_root_dir,
        'tools.my_auth.on': True,
        'tools.sessions.on': True,
        'tools.sessions.name': 'my_auth'
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
    },
    '/.well-known':
    {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': '.well-known',
    },
}

cherrypy.config.update({
    'server.socket_host': '127.0.0.1',
    'server.socket_port': args.port,
    'requests.show_tracebacks': False,
    'log.access_file': ACCESS_LOG,
    'log.error_file': ERROR_LOG})

cherrypy.quickstart(g_app, config=conf)
