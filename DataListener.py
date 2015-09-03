import json
import os
import signal
import socket
import sys
import ExertDb

g_debug = False
g_rootDir = os.path.dirname(os.path.realpath(__file__))

def Log(str):
	global g_debug
	global g_rootDir

	logFileName = os.path.join(g_rootDir, "DataListener.log")
	with open(logFileName, 'a') as f:
		if g_debug:
			print str
		f.write(str + "\n")
		f.close()

def signal_handler(signal, frame):
	Log("Exiting...")
	sys.exit(0)

class DataListener(object):
	db = None
	running = True

	def __init__(self, db):
		self.db = db
		self.db.create()
		self.notMetaData = [ "DeviceId", "ActivityId", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
		super(DataListener, self).__init__()

	def parseJsonStr(self, str):
		try:
			decoder = json.JSONDecoder()
			decodedObj = json.loads(str)

			# Parse required identifiers
			deviceId = decodedObj["DeviceId"]
			activityId = decodedObj["ActivityId"]
			
			# Parse optional identifiers
			userName = ""
			try:
				userName = decodedObj["User Name"]
			except:
				pass

			# Parse the location data
			lat = decodedObj["Latitude"]
			lon = decodedObj["Longitude"]
			alt = decodedObj["Altitude"]
			self.db.insertLocation(deviceId, activityId, lat, lon, alt)

			# Clear the metadata
			self.db.clearMetadata(deviceId)

			# Parse the metadata
			for item in decodedObj.iteritems():
				key = item[0]
				value = item[1]
				if not key in self.notMetaData:
					self.db.insertMetadata(deviceId, activityId, key, value)
				
			# Update the user device association
			if len(userName):
				userDbId = self.db.getUserIdFromUserName(userName)
				deviceDbId = self.db.getDeviceIdFromDeviceStr(deviceId)
				self.db.updateDevice(deviceDbId, userDbId)
		except ValueError:
			Log("ValueError in JSON data.")
		except KeyError, e:
			Log("KeyError - reason " + str(e) + ".")
		except:
			Log("Error parsing JSON data.")

	def readLine(self, sock):
		while self.running:
			data, addr = sock.recvfrom(1024)
			return data
		return None

	def run(self):
		UDP_IP = ""
		UDP_PORT = 5150

		Log("Starting the app listener")

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((UDP_IP, UDP_PORT))

		while self.running:
			line = self.readLine(sock)
			if line:
				self.parseJsonStr(line)

		Log("App listener stopped")

def Start():
	global g_rootDir
	
	Log("Opening the database in " + g_rootDir)
	db = ExertDb.Database(g_rootDir)
	
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
			g_rootDir = sys.argv[i]

	if g_debug:
		Start()
	else:
		import daemon

		with daemon.DaemonContext():
			Start()
