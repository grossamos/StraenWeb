import os
import sqlite3
import sys

class Location(object):
	def __init__(self):
		self.latitude = 0.0
		self.longitude = 0.0
		super(Location, self).__init__()

class Database(object):
	dbFile = ""

	def __init__(self, rootDir):
		self.dbFile = os.path.join(rootDir, 'exert.sqlite')
		super(Database, self).__init__()

	def logError(self, str):
		pass

	def execute(self, sql):
		try:
			con = sqlite3.connect(self.dbFile)
			with con:
				cur = con.cursor()
				cur.execute(sql)
				return cur.fetchall()
		except:
			self.logError("Error opening the database")
		finally:
			if con:
				con.close()
		return None

	def quoteIdentifier(self, s, errors="strict"):
		encodable = s.encode("utf-8", errors).decode("utf-8")
		null_index = encodable.find("\x00")
		if null_index >= 0:
			return ""
		return "\"" + encodable.replace("\"", "\"\"") + "\""

	def create(self):
		try:
			self.execute("create table location (id integer primary key, deviceId integer, activityId integer, latitude double, longitude double, altitude double)")
		except:
			pass

		try:
			self.execute("create table metadata (id integer primary key, deviceId integer, activityId integer, key text, value double)")
		except:
			pass

		try:
			self.execute("create table user (id integer primary key, username text, firstname text, lastname text, hash text)")
		except:
			pass

		try:
			self.execute("create table followedBy (id integer primary key, userId integer, followerId integer, approved integer)")
		except:
			pass

		try:
			self.execute("create table following (id integer primary key, userId integer, followingId integer, approved integer)")
		except:
			pass

		try:
			self.execute("create table device (id integer primary key, device text, userId integer)")
		except:
			pass
	
	def insertUser(self, username, firstname, lastname, hash):
		if username is None:
			self.logError("Unexpected empty object")
			return False
		if firstname is None:
			self.logError("Unexpected empty object")
			return False
		if lastname is None:
			self.logError("Unexpected empty object")
			return False
		if hash is None:
			self.logError("Unexpected empty object")
			return False
		if len(username) == 0:
			self.logError("username too short")
			return False
		if len(firstname) == 0:
			self.logError("firstname too short")
			return False
		if len(lastname) == 0:
			self.logError("lastname too short")
			return False
		if len(hash) == 0:
			self.logError("hash too short")
			return False

		try:
			sql = "insert into user values(NULL, " + self.quoteIdentifier(username) + ", " + self.quoteIdentifier(firstname) + ", " + self.quoteIdentifier(lastname) + ", '" + hash + "')"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return False

	def getUserHash(self, username):
		if username is None:
			self.logError("Unexpected empty object")
			return 0
		if len(username) == 0:
			self.logError("username too short")
			return 0

		try:
			sql = "select hash from user where username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def insertToFollowedByList(self, username, followedByName):
		if username is None:
			self.logError("Unexpected empty object")
			return False
		if followedByName is None:
			self.logError("Unexpected empty object")
			return False

		try:
			userId = self.getUserIdFromUserName(username)
			followerId = self.getUserIdFromUserName(followedByName)

			sql = "insert into followedBy values(NULL, " + userId + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return False

	def insertToFollowingList(self, username, followingName):
		if username is None:
			self.logError("Unexpected empty object")
			return False
		if followingName is None:
			self.logError("Unexpected empty object")
			return False

		try:
			userId = self.getUserIdFromUserName(username)
			followerId = self.getUserIdFromUserName(followingName)
			
			sql = "insert into following values(NULL, " + userId + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return False

	def getUserIdFromUserName(self, username):
		if username is None:
			self.logError("Unexpected empty object")
			return 0
		if len(username) == 0:
			self.logError("username too short")
			return 0

		try:
			sql = "select id from user where username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def insertDevice(self, deviceId, userId):
		if deviceStr is None:
			self.logError("Unexpected empty object")
			return None
		if len(deviceStr) == 0:
			self.logError("Device ID too short")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None
	
	def getDeviceIdFromDeviceStr(self, deviceStr):
		if deviceStr is None:
			self.logError("Unexpected empty object")
			return None
		if len(deviceStr) == 0:
			self.logError("Device ID too short")
			return None

		try:
			sql = "select id from device where device = " + self.quoteIdentifier(deviceStr)
			rows = self.execute(sql)
			if rows is None:
				return None
			if len(rows) == 0:
				sql = "insert into device values(NULL, " + self.quoteIdentifier(deviceStr) + ", 0)"
				rows = self.execute(sql)
				sql = "select id from device where device = " + self.quoteIdentifier(deviceStr)
				rows = self.execute(sql)
			return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def getDeviceFromUsername(self, username):
		if username is None:
			self.logError("Unexpected empty object")
			return None
		if len(username) == 0:
			self.logError("username too short")
			return None

		try:
			sql = "select device.id, device.device from device inner join user on device.userId=user.id and user.username = " + self.quoteIdentifier(username)
			rows = self.execute(sql)
			if len(rows) == 0:
				return None
			return rows[0][0],rows[0][1]
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def updateDevice(self, deviceId, userId):
		try:
			sql = "update device set userId = " + str(userId) + " where id = " + str(deviceId)
			rows = self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def getLatestActivityIdForDevice(self, deviceId):
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None

		try:
			sql = "select max(activityId) from location where deviceId = " + str(deviceId)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return 0

	def clearMetadata(self, deviceStr):
		if deviceStr is None:
			self.logError("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			self.logError("Device ID too short")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			if deviceId is not None:
				sql = "delete from metadata where deviceId = " + str(deviceId)
				self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return

	def insertMetadata(self, deviceStr, activityId, key, value):
		if deviceStr is None:
			self.logError("Unexpected empty object")
			return
		if activityId is None:
			self.logError("Unexpected empty object")
			return
		if key is None:
			self.logError("Unexpected empty object")
			return
		if value is None:
			self.logError("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			self.logError("Device ID too short")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			sql = "insert into metadata values(NULL, " + str(deviceId) + ", " + str(activityId) + ", '" + key + "', " + str(value) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return

	def getMetaData(self, key, deviceId, activityId):
		if key is None:
			self.logError("Unexpected empty object")
			return None
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None
		if activityId is None:
			self.logError("Unexpected empty object")
			return None

		try:
			sql = "select value from metadata where key = " + self.quoteIdentifier(key) + " and deviceId = " + str(deviceId) + " and activityId = " + str(activityId) + " limit 1"
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def getLatestMetaData(self, key, deviceId):
		if key is None:
			self.logError("Unexpected empty object")
			return None
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None

		try:
			activityId = self.getLatestActivityIdForDevice(deviceId)
			if activityId > 0:
				return self.getMetaData(key, deviceId, activityId)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return None

	def insertLocation(self, deviceStr, activityId, latitude, longitude, altitude):
		if deviceStr is None:
			self.logError("Unexpected empty object")
			return
		if activityId is None:
			self.logError("Unexpected empty object")
			return
		if latitude is None:
			self.logError("Unexpected empty object")
			return
		if longitude is None:
			self.logError("Unexpected empty object")
			return
		if altitude is None:
			self.logError("Unexpected empty object")
			return

		try:
			deviceId = self.getDeviceIdFromDeviceStr(deviceStr)
			sql = "insert into location values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return

	def listLocations(self, deviceId, activityId):
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None
		if activityId is None:
			self.logError("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select latitude, longitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
			rows = self.execute(sql)
			if rows != None:
				for row in rows:
					location = Location()
					location.latitude = row[0]
					location.longitude = row[1]
					locations.append(location)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return locations

	def listLastLocations(self, deviceId, activityId, num):
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None
		if activityId is None:
			self.logError("Unexpected empty object")
			return None
		if num is None:
			self.logError("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select count(*) from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				rowCount = int(rows[0][0])
				newRows = rowCount - num
				if newRows > 0:
					sql = "select latitude, longitude from location where deviceId = " + str(deviceId) + " and activityId = " + str(activityId) + " order by id desc limit " + str(num)
					rows = self.execute(sql)
					if rows != None:
						for row in rows:
							location = Location()
							location.latitude = row[0]
							location.longitude = row[1]
							locations.append(location)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return locations

	def listLocationsForLatestActivity(self, deviceId):
		if deviceId is None:
			self.logError("Unexpected empty object")
			return None

		locations = []

		try:
			activityId = self.getLatestActivityIdForDevice(deviceId)
			if activityId > 0:
				locations = self.listLocations(deviceId, activityId)
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return locations

	def listUsersFollowing(self, username):
		if username is None:
			self.logError("Unexpected empty object")
			return None
		if len(username) == 0:
			self.logError("username too short")
			return None

		following = []
		
		try:
			userId = self.getUserIdFromUserName(username)
			if userId != None:
				sql = "select * from following where userId = " + str(userId)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						following.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return following

	def listUsersFollowedBy(self, username):
		if username is None:
			self.logError("Unexpected empty object")
			return None
		if len(username) == 0:
			self.logError("username too short")
			return None

		followedBy = []

		try:
			userId = self.getUserIdFromUserName(username)
			if userId != None:
				sql = "select * from followedBy where userId = " + str(userId)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						followedBy.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.logError(sys.exc_info()[0])
		return followedBy

