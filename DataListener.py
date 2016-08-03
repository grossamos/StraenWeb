import datetime
import json
import os
import signal
import socket
import sys
import traceback
import time
import ExertDb

g_debug = False
g_root_dir = os.path.dirname(os.path.realpath(__file__))

CADENCE_KEY    = "Cadence"
HEART_RATE_KEY = "Heart Rate"
POWER_KEY      = "Power"

CADENCE_DB_KEY    = 1
HEART_RATE_DB_KEY = 2
POWER_DB_KEY      = 3

def Log(str):
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

def signal_handler(signal, frame):
	Log("Exiting...")
	sys.exit(0)

class DataListener(object):
	db = None
	running = True

	def __init__(self, db):
		self.db = db
		self.db.create()
		self.not_meta_data = [ "DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
		super(DataListener, self).__init__()

	def parse_json_str(self, str):
		try:
			decoder = json.JSONDecoder()
			decoded_obj = json.loads(str)

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
				user_db_id = self.db.getUserIdFromUserName(user_name)
				device_db_id = self.db.getDeviceIdFromDeviceStr(device_id)
				self.db.updateDevice(device_db_id, user_db_id)
		except ValueError, e:
			Log("ValueError in JSON data - reason " + str(e) + ".")
		except KeyError, e:
			Log("KeyError in JSON data - reason " + str(e) + ".")
		except:
			Log("Error parsing JSON data.")
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			#traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

	def read_line(self, sock):
		while self.running:
			data, addr = sock.recvfrom(1024)
			return data
		return None

	def run(self):
		UDP_IP = ""
		UDP_PORT = 5150

		Log("Starting the app listener")

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.bind((UDP_IP, UDP_PORT))

			while self.running:
				line = self.read_line(sock)
				if line:
					self.parse_json_str(line)
		except:
			Log("Unhandled exception in run().")

		Log("App listener stopped")

def Start():
	global g_root_dir
	
	Log("Opening the database in " + g_root_dir)
	db = ExertDb.ExertDb(g_root_dir)
	
	listener = DataListener(db)
	listener.run()

if __name__ == "__main__":

	signal.signal(signal.SIGINT, signal_handler)

	for i in range(0,len(sys.argv)):
		arg = sys.argv[i]
		
		if arg == 'debug' or arg == '--debug':
			g_debug = True
		elif arg == 'rootdir' or arg == '--rootdir':
			i = i + 1
			g_root_dir = sys.argv[i]

	if g_debug:
		Start()
	else:
		import daemon

		with daemon.DaemonContext():
			Start()
