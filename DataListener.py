import argparse
import cgi
import datetime
import json
import os
import re
import signal
import socket
import sys
import threading
import time
import traceback
import SocketServer
import BaseHTTPServer
import ExertDb

g_debug = False
g_data_log = False
g_root_dir = os.path.dirname(os.path.realpath(__file__))
g_not_meta_data = [ "DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
g_listener = None

CADENCE_KEY    = "Cadence"
HEART_RATE_KEY = "Heart Rate"
POWER_KEY      = "Power"

CADENCE_DB_KEY    = 1
HEART_RATE_DB_KEY = 2
POWER_DB_KEY      = 3

def log_info(str):
	global g_debug
	global g_root_dir

	log_file_name = os.path.join(g_root_dir, "DataListener.log")
	with open(log_file_name, 'a') as f:
		current_time = datetime.datetime.now()
		log_str = current_time.isoformat() + ": " + str
		f.write(log_str + "\n")
		f.close()
		if g_debug:
			print log_str

def log_data(str):
	global g_debug
	global g_root_dir
	
	log_file_name = os.path.join(g_root_dir, "DataListenerInput.log")
	with open(log_file_name, 'a') as f:
		current_time = datetime.datetime.now()
		log_str = current_time.isoformat() + ": " + str
		f.write(log_str + "\n")
		f.close()
		if g_debug:
			print log_str

def signal_handler(signal, frame):
	log_info("Exiting...")
	if g_listener is not None:
		g_listener.shutdown()
	sys.exit(0)

def parse_json_str(db, jsonStr):
	try:
		decoder = json.JSONDecoder()
		decoded_obj = json.loads(jsonStr)

		# Parse required identifiers.
		device_str = decoded_obj["DeviceId"]
		activity_id = decoded_obj["ActivityId"]
		device_id = db.retrieve_device_id_from_device_str(device_str)

		# Parse optional identifiers.
		user_name = ""
		try:
			user_name = decoded_obj["User Name"]
		except:
			pass

		# Parse the location data.
		lat = decoded_obj["Latitude"]
		lon = decoded_obj["Longitude"]
		alt = decoded_obj["Altitude"]
		db.create_location(device_id, activity_id, lat, lon, alt)

		# Clear the old metadata.
		#db.clear_metadata_for_activity(device_id, activity_id)

		# Parse the metadata looking for the timestamp.
		date_time = time.time()
		try:
			time_str = decoded_obj["Time"]
			date_time = int(time_str)
		except:
			pass
		
		# Parse the rest of the data, which will be a combination of metadata and sensor data.
		for item in decoded_obj.iteritems():
			key = item[0]
			value = item[1]
			if not key in g_not_meta_data:
				if key == CADENCE_KEY:
					db.create_sensordata(device_id, activity_id, date_time, CADENCE_DB_KEY, value)
				elif key == HEART_RATE_KEY:
					db.create_sensordata(device_id, activity_id, date_time, HEART_RATE_DB_KEY, value)
				elif key == POWER_KEY:
					db.create_sensordata(device_id, activity_id, date_time, POWER_DB_KEY, value)
				else:
					db.create_metadata(device_id, activity_id, date_time, key, value)

		# Update the user device association
		if len(user_name):
			user_id = db.retrieve_user_id_from_username(user_name)
			db.update_device(device_id, user_id)
	except ValueError, e:
		log_info("ValueError in JSON data - reason " + str(e) + ".")
	except KeyError, e:
		log_info("KeyError in JSON data - reason " + str(e) + ".")
	except:
		log_info("Error parsing JSON data." + str(jsonStr))
		#exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
		#traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		if re.search('/api/v1/addlocations', self.path) != None:
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'multipart/form-data':
				post_vars = cgi.parse_multipart(self.rfile, pdict)
			elif ctype == 'application/x-www-form-urlencoded':
				length = int(self.headers.getheader('content-length'))
				post_vars = cgi.parse_qs(self.rfile.read(length), keep_blank_values = 1)
				json_strs = post_vars.keys()
				for json_str in json_strs:
					parse_json_str(self.db, json_str)
			else:
				post_vars = {}

			self.send_response(200)
			self.end_headers()

			self.wfile.write("Content-type: text/html<BR><BR>");
			self.wfile.write("<HTML>POST OK.<BR><BR>");
		else:
			self.send_error(404, 'File Not Found: %s' % self.path)

	def do_GET(self):
		self.send_response(404, 'Bad Request: resource not found')
		self.send_header('Content-Type', 'application/json')
		self.end_headers()

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	allow_reuse_address = True
	db = None
	port = 8080
 
	def __init__(self, db, port):
		self.db = db
		self.db.create()
		self.port = port
		BaseHTTPServer.HTTPServer.__init__(self, ("", self.port), HTTPRequestHandler)
	
	def shutdown(self):
		self.socket.close()
		BaseHTTPServer.HTTPServer.shutdown(self)

class UdpDataListener(object):
	db = None
	port = 5150
	running = True

	def __init__(self, db, port):
		self.db = db
		self.db.create()
		self.port = port
		super(UdpDataListener, self).__init__()

	def read_line(self, sock):
		while self.running:
			data, addr = sock.recvfrom(1024)
			return data
		return None

	def listen_for_rest_messages(self):
		pass

	def listen_for_udp_packets(self):
		log_info("Starting the app listener")

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.bind(("", self.port))

			while self.running:
				line = self.read_line(sock)
				if line:
					parse_json_str(self.db, line)
					if g_data_log:
						log_data(line)
		except:
			log_info("Unhandled exception in run().")

		log_info("App listener stopped")

	def run(self):
		self.listen_for_udp_packets()

	def shutdown(self):
		self.running = False

def Start(protocol, port):
	global g_root_dir

	log_info("Opening the database in " + g_root_dir)
	db = ExertDb.ExertDb(g_root_dir)

	if protocol == "rest":
		g_listener = ThreadedHTTPServer(db, port)
		g_listener.serve_forever()
	else:
		g_listener = UdpDataListener(db, port)
		g_listener.run()

if __name__ == "__main__":

	signal.signal(signal.SIGINT, signal_handler)

	# Parse command line options.
	parser = argparse.ArgumentParser()
	parser.add_argument("--rootdir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory for database and logs", required=False)
	parser.add_argument("--protocol", type=str, action="store", default="udp", help="udp|rest", required=False)
	parser.add_argument("--port", type=int, action="store", default=8080, help="Port on which to listen", required=False)
	parser.add_argument("--debug", action="store_true", default=False, help="", required=False)
	parser.add_argument("--datalog", action="store_true", default=False, help="", required=False)

	try:
		args = parser.parse_args()
		g_root_dir = args.rootdir
		g_debug = args.debug
		g_data_log = args.datalog
	except IOError as e:
		parser.error(e)
		sys.exit(1)

	if g_debug:
		Start(args.protocol, args.port)
	else:
		import daemon

		with daemon.DaemonContext():
			Start(args.protocol, args.port)
