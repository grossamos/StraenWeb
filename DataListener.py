import os
import signal
import socket
import daemon
import ExertDb

class DataListener(object):
	running = True

	def __init__(self, db):
		self.db = db
		self.db.create()
		self.notMetaData = [ "DeviceId", "ActivityId", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy" ]
		super(DataListener, self).__init__()

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
			self.db.insertLocation(deviceId, activityId, lat, lon, alt)

			# Clear the metadata
			self.db.clearMetadata(deviceId)

			# Parse the metadata
			for item in decodedObj.iteritems():
				key = item[0]
				value = item[1]
				if not key in self.notMetaData:
					self.db.insertMetadata(deviceId, activityId, key, value)
		except ValueError:
			print "ValueError in JSON data."
		except KeyError, e:
			print "KeyError - reason " + str(e) + "."
		except:
			print "Error parsing JSON data."

	def readLine(self, sock):
		while self.running:
			data, addr = sock.recvfrom(1024)
			return data
		return None

	def run(self):
		UDP_IP = ""
		UDP_PORT = 5150

		print "Starting app listener"

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((UDP_IP, UDP_PORT))

		while self.running:
			line = self.readLine(sock)
			if line:
				self.parseJsonStr(line)

		print "App listener stopped"

if __name__ == "__main__":
	with daemon.DaemonContext():
		dir = os.path.dirname(os.path.realpath(__file__))
		dbFile = os.path.join(dir, 'exert.sqlite')
		db = ExertDb.Database(dbFile)

		listener = DataListener(db)
		listener.run()
