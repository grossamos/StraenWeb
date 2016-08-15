import argparse
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
import ExertDb

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn

g_debug = False
g_data_log = False
g_root_dir = os.path.dirname(os.path.realpath(__file__))

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
	sys.exit(0)

class HTTPRequestHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		if None != re.search('/api/v1/addlocation/*', self.path):
			self.send_response(200)
			self.end_headers()
		else:
			self.send_response(403)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
		return
 
	def do_GET(self):
		self.send_response(404, 'Bad Request: resource not found')
		self.send_header('Content-Type', 'application/json')
		self.end_headers()
		return
 
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	allow_reuse_address = True
 
	def shutdown(self):
		self.socket.close()
		HTTPServer.shutdown(self)

class UdpDataListener(object):
	db = None
	port = 5150
	running = True

	def __init__(self, db, port):
		self.db = db
		self.db.create()
		self.port = port
		self.not_meta_data = [ "DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
		super(UdpDataListener, self).__init__()

	def parse_json_str(self, jsonStr):
		try:
			decoder = json.JSONDecoder()
			decoded_obj = json.loads(jsonStr)

			# Parse required identifiers.
			device_str = decoded_obj["DeviceId"]
			activity_id = decoded_obj["ActivityId"]
			device_id = self.db.retrieve_device_id_from_device_str(device_str)

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
			self.db.create_location(device_id, activity_id, lat, lon, alt)
			
			# Clear the old metadata.
			#self.db.clear_metadata_for_activity(device_id, activity_id)

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
				if not key in self.not_meta_data:
					if key == CADENCE_KEY:
						self.db.create_sensordata(device_id, activity_id, date_time, CADENCE_DB_KEY, value)
					elif key == HEART_RATE_KEY:
						self.db.create_sensordata(device_id, activity_id, date_time, HEART_RATE_DB_KEY, value)
					elif key == POWER_KEY:
						self.db.create_sensordata(device_id, activity_id, date_time, POWER_DB_KEY, value)
					else:
						self.db.create_metadata(device_id, activity_id, date_time, key, value)

			# Update the user device association
			if len(user_name):
				user_id = self.db.retrieve_user_id_from_username(user_name)
				self.db.update_device(device_id, user_id)
		except ValueError, e:
			log_info("ValueError in JSON data - reason " + str(e) + ".")
		except KeyError, e:
			log_info("KeyError in JSON data - reason " + str(e) + ".")
		except:
			log_info("Error parsing JSON data." + str(jsonStr))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			#traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

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
					self.parse_json_str(line)
					if g_data_log:
						log_data(line)
		except:
			log_info("Unhandled exception in run().")

		log_info("App listener stopped")

	def run(self):
		self.listen_for_udp_packets()

def Start(protocol, port):
	global g_root_dir

	log_info("Opening the database in " + g_root_dir)
	db = ExertDb.ExertDb(g_root_dir)

	if protocol == "rest":
		server = ThreadedHTTPServer(("", port), HTTPRequestHandler) 
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.daemon = True
		server_thread.start()
 		server_thread.join()
	else:
		listener = UdpDataListener(db, port)
		listener.run()

if __name__ == "__main__":

	signal.signal(signal.SIGINT, signal_handler)

	# Parse command line options.
	parser = argparse.ArgumentParser()
	parser.add_argument("--rootdir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory for database and logs", required=False)
	parser.add_argument("--protocol", type=str, action="store", default="udp", help="udp|rest", required=False)
	parser.add_argument("--port", type=int, action="store", default=5150, help="Port on which to listen", required=False)
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
