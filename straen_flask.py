# Copyright 2018 Michael J Simms
"""Main application - if using flask, contains all web page handlers"""

import argparse
import functools
import json
import logging
import mako
import os
import signal
import sys
import traceback
import flask

import Api
import ApiException
import App
import DataMgr
import AnalysisScheduler
import ImportScheduler
import SessionException
import SessionMgr
import UserMgr
import WorkoutPlanGeneratorScheduler


CSS_DIR = 'css'
DATA_DIR = 'data'
JS_DIR = 'js'
IMAGES_DIR = 'images'
MEDIA_DIR = 'media'
ERROR_LOG = 'error.log'


g_flask_app = flask.Flask(__name__)
g_flask_app.secret_key = 'UB2s60qJrithXHt2w71f'
g_flask_app.url_map.strict_slashes = False
g_root_dir = os.path.dirname(os.path.abspath(__file__))
g_app = None
g_session_mgr = SessionMgr.FlaskSessionMgr()


def signal_handler(signal, frame):
    global g_app

    print("Exiting...")
    if g_app is not None:
        g_app.terminate()
    sys.exit(0)

def login_requred(function_to_protect):
    @functools.wraps(function_to_protect)
    def wrapper(*args, **kwargs):
        global g_session_mgr
        user = g_session_mgr.get_logged_in_user()
        if user:
            return function_to_protect(*args, **kwargs)
        return flask.redirect(flask.url_for('login'))
    return wrapper

@g_flask_app.route('/css/<file_name>')
def css(file_name):
    """Returns the CSS page."""
    try:
        return flask.send_from_directory(CSS_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + css.__name__)
    return g_app.render_error()

@g_flask_app.route('/data/<file_name>')
def data(file_name):
    """Returns the data page."""
    try:
        return flask.send_from_directory(DATA_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + data.__name__)
    return g_app.render_error()

@g_flask_app.route('/js/<file_name>')
def js(file_name):
    """Returns the JS page."""
    try:
        return flask.send_from_directory(JS_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + js.__name__)
    return g_app.render_error()

@g_flask_app.route('/images/<file_name>')
def images(file_name):
    """Returns images."""
    try:
        return flask.send_from_directory(IMAGES_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + images.__name__)
    return g_app.render_error()

@g_flask_app.route('/media/<file_name>')
def media(file_name):
    """Returns media files (icons, etc.)."""
    try:
        return flask.send_from_directory(MEDIA_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + media.__name__)
    return g_app.render_error()

@g_flask_app.route('/stats')
def stats():
    """Renders the internal statistics page."""
    try:
        return g_app.stats()
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + stats.__name__)
    return g_app.render_error()

@g_flask_app.route('/error')
def error(error_str=None):
    """Renders the error page."""
    try:
        return g_app.render_error(error_str)
    except:
        pass
    return g_app.render_error()

@g_flask_app.route('/live/<device_str>')
def live(device_str):
    """Renders the map page for the current activity from a single device."""
    try:
        return g_app.live(device_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live.__name__)
    return g_app.render_error()

@g_flask_app.route('/live_user/<user_str>')
def live_user(user_str):
    """Renders the map page for the current activity from a specified user."""
    try:
        return g_app.live_user(user_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live_user.__name__)
    return g_app.render_error()

@g_flask_app.route('/activity/<activity_id>')
def activity(activity_id):
    """Renders the details page for an activity."""
    try:
        return g_app.activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + activity.__name__)
    return g_app.render_error()

@g_flask_app.route('/edit_activity/<activity_id>')
def edit_activity(activity_id):
    """Renders the edit page for an activity."""
    try:
        return g_app.edit_activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + edit_activity.__name__)
    return g_app.render_error()

@g_flask_app.route('/device/<device_str>')
def device(device_str):
    """Renders the map page for a single device."""
    try:
        return g_app.device(device_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device.__name__)
    return g_app.render_error()

@g_flask_app.route('/my_activities')
@login_requred
def my_activities():
    """Renders the list of the specified user's activities."""
    try:
        return g_app.my_activities()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + my_activities.__name__)
    return g_app.render_error()

@g_flask_app.route('/all_activities')
@login_requred
def all_activities():
    """Renders the list of all activities the specified user is allowed to view."""
    try:
        return g_app.all_activities()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + all_activities.__name__)
    return g_app.render_error()

@g_flask_app.route('/all_records/<activity_type>/<record_name>')
@login_requred
def all_records(self, activity_type, record_name):
    """Renders the list of records for the specified user and record type."""
    try:
        return g_app.all_records(activity_type, record_name)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + all_records.__name__)
    return self.error()

@g_flask_app.route('/record_progression/<activity_type>/<record_name>')
@login_requred
def record_progression(self, activity_type, record_name):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    try:
        return g_app.record_progression(activity_type, record_name)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + record_progression.__name__)
    return self.error()

@g_flask_app.route('/workouts')
@login_requred
def workouts():
    """Renders the workouts view."""
    try:
        return g_app.workouts()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workouts.__name__)
    return g_app.render_error()

@g_flask_app.route('/workout/<workout_id>')
@login_requred
def workout(workout_id):
    """Renders the view for an individual workout."""
    try:
        return g_app.workout(workout_id)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workout.__name__)
    return g_app.render_error()

@g_flask_app.route('/statistics')
@login_requred
def statistics():
    """Renders the statistics view."""
    try:
        return g_app.stats()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + statistics.__name__)
    return g_app.render_error()

@g_flask_app.route('/gear')
@login_requred
def gear():
    """Renders the list of all gear belonging to the logged in user."""
    try:
        return g_app.gear()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + gear.__name__)
    return g_app.render_error()

@g_flask_app.route('/service_history/<gear_id>')
@login_requred
def service_history(gear_id):
    """Renders the service history for a particular piece of gear."""
    try:
        return g_app.service_history(gear_id)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + service_history.__name__)
    return g_app.render_error()

@g_flask_app.route('/friends')
@login_requred
def friends():
    """Renders the list of users who are friends with the logged in user."""
    try:
        return g_app.friends()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + friends.__name__)
    return g_app.render_error()

@g_flask_app.route('/device_list')
@login_requred
def device_list():
    """Renders the list of a user's devices."""
    try:
        return g_app.device_list()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device_list.__name__)
    return g_app.render_error()

@g_flask_app.route('/upload/<ufile>')
@login_requred
def upload(ufile):
    """Processes an upload request."""
    try:
        return g_app.upload(ufile)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + upload.__name__)
    return g_app.render_error()

@g_flask_app.route('/manual_entry/<activity_type>')
@login_requred
def manual_entry(activity_type):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    try:
        return g_app.manual_entry(activity_type)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + manual_entry.__name__)
    return g_app.render_error()

@g_flask_app.route('/import_activity')
@login_requred
def import_activity():
    """Renders the import page."""
    try:
        return g_app.import_activity()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + import_activity.__name__)
    return g_app.render_error()

@g_flask_app.route('/task_status')
@login_requred
def task_status():
    """Renders the import status page."""
    try:
        return g_app.task_status()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + task_status.__name__)
    return g_app.render_error()

@g_flask_app.route('/analysis_status')
@login_requred
def analysis_status():
    """Renders the analysis status page."""
    try:
        return g_app.analysis_status()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + analysis_status.__name__)
    return g_app.render_error()

@g_flask_app.route('/profile')
@login_requred
def profile():
    """Renders the user's profile page."""
    try:
        return g_app.profile()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + profile.__name__)
    return g_app.render_error()

@g_flask_app.route('/settings')
@login_requred
def settings():
    """Renders the user's settings page."""
    try:
        return g_app.settings()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + settings.__name__)
    return g_app.render_error()

@g_flask_app.route('/login')
def login():
    """Renders the login page."""
    try:
        return g_app.login()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        return g_app.render_error()
    return g_app.render_error()

@g_flask_app.route('/create_login')
def create_login():
    """Renders the create login page."""
    try:
        return g_app.create_login()
    except:
        return g_app.render_error()
    return g_app.render_error()

@g_flask_app.route('/logout')
def logout():
    """Ends the logged in session."""
    try:
        return g_app.logout()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except SessionException.SessionTerminatedException as e:
        response = flask.redirect(e.url, code=302)
        response.set_cookie(Keys.SESSION_KEY, '', expires=0)
        response.delete_cookie(username)
        return response
    except:
        return g_app.render_error()
    return g_app.render_error()

@g_flask_app.route('/about')
def about():
    """Renders the about page."""
    result = ""
    try:
        result = g_app.about()
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/status')
def status():
    """Renders the status page. Used as a simple way to tell if the site is up."""
    result = ""
    try:
        result = g_app.status()
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/ical/<calendar_id>')
def ical(calendar_id):
    """Returns the ical calendar with the specified ID."""
    result = ""
    code = 200
    try:
        handled, response = g_app.ical(calendar_id)
        if not handled:
            code = 400
        return response
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/api/<version>/<method>', methods = ['GET','POST'])
def api(version, method):
    """Endpoint for API calls."""
    response = ""
    code = 200
    try:
        # Get the logged in user.
        user_id = None
        username = g_app.user_mgr.get_logged_in_user()
        if username is not None:
            user_id, _, _ = g_app.user_mgr.retrieve_user(username)

        # The the API params.
        verb = "POST"
        if flask.request.method == 'GET':
            verb = "GET"
            params = flask.request.args
        elif flask.request.data:
            params = json.loads(flask.request.data)
        else:
            params = ""

        # Process the API request.
        if version == '1.0':
            handled, response = g_app.api(user_id, verb, method, params)
            if not handled:
                response = "Failed to handle request: " + str(method)
                g_app.log_error(response)
                code = 400
            else:
                code = 200
        else:
            g_app.log_error("Failed to handle request for api version " + version)
            code = 400
    except ApiException.ApiException as e:
        g_app.log_error(e.message)
        code = e.code
    except SessionException.SessionTerminatedException as e:
        response = g_app.make_response("")
        response.set_cookie(Keys.SESSION_KEY, '', expires=0)
        response.delete_cookie(Keys.SESSION_KEY)
        return response
    except Exception as e:
        response = str(e.args[0])
        g_app.log_error(response)
        code = 500
    except:
        code = 500
    return response, code

@g_flask_app.route('/')
def index():
    """Renders the index page."""
    return login()

def main():
    """Entry point for the flask version of the app."""
    global g_app
    global g_flask_app

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False, help="Prevents the app from going into the background.", required=False)
    parser.add_argument("--profile", action="store_true", default=False, help="Enables application profiling.", required=False)
    parser.add_argument("--host", default="", help="Host name on which users will access this website.", required=False)
    parser.add_argument("--hostport", type=int, default=5000, help="Port on which users will access this website.", required=False)
    parser.add_argument("--https", action="store_true", default=False, help="Runs the app as HTTPS.", required=False)
    parser.add_argument("--googlemapskey", default="", help="API key for Google Maps. If not provided OpenStreetMap will be used.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if args.https:
        protocol = "https"
    else:
        protocol = "http"

    if len(args.host) == 0:
        if args.debug:
            args.host = "127.0.0.1"
        else:
            args.host = "straen-app.com"
        print("Hostname not provided, will use " + args.host)

    root_url = protocol + "://" + args.host
    if args.hostport > 0:
        root_url = root_url + ":" + str(args.hostport)
    print("Root URL is " + root_url)

    signal.signal(signal.SIGINT, signal_handler)
    mako.collection_size = 100
    mako.directories = "templates"

    session_mgr = SessionMgr.FlaskSessionMgr()
    user_mgr = UserMgr.UserMgr(session_mgr)
    data_mgr = DataMgr.DataMgr(root_url, AnalysisScheduler.AnalysisScheduler(), ImportScheduler.ImportScheduler(), WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler())
    g_app = App.App(user_mgr, data_mgr, g_root_dir, root_url, args.googlemapskey, args.profile, args.debug)

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    g_flask_app.run(debug=args.debug)

if __name__ == '__main__':
    main()
