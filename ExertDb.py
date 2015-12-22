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
		self.logFileName = os.path.join(rootDir, 'ExertDb.log')
		super(Database, self).__init__()

	def log_error(self, str):
		with open(self.logFileName, 'a') as f:
			f.write(str + "\n")
			f.close()

	def execute(self, sql):
		try:
			con = sqlite3.connect(self.dbFile)
			with con:
				cur = con.cursor()
				cur.execute(sql)
				return cur.fetchall()
		except:
			self.log_error("Database error:\n\tfile = " + dbFile + "\n\tsql = " + sql)
		finally:
			if con:
				con.close()
		return None

	def quote_identifier(self, s, errors="strict"):
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
			self.execute("create table metadata (id integer primary key, deviceId integer, activityId integer, time integer, key text, value double)")
		except:
			pass

		try:
			self.execute("create table user (id integer primary key, username text, realname text, hash text)")
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
	
	def insert_user(self, username, realname, hash):
		if username is None:
			self.log_error("Unexpected empty object")
			return False
		if realname is None:
			self.log_error("Unexpected empty object")
			return False
		if hash is None:
			self.log_error("Unexpected empty object")
			return False
		if len(username) == 0:
			self.log_error("username too short")
			return False
		if len(realname) == 0:
			self.log_error("realname too short")
			return False
		if len(hash) == 0:
			self.log_error("hash too short")
			return False

		try:
			sql = "insert into user values(NULL, " + self.quote_identifier(username) + ", " + self.quote_identifier(realname) + ", '" + hash + "')"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def get_user_hash(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return 0
		if len(username) == 0:
			self.log_error("username too short")
			return 0
		
		try:
			sql = "select hash from user where username = " + self.quote_identifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return 0

	def insert_to_followed_by_list(self, username, followedByName):
		if username is None:
			self.log_error("Unexpected empty object")
			return False
		if followedByName is None:
			self.log_error("Unexpected empty object")
			return False

		try:
			userId = self.get_user_id_from_username(username)
			followerId = self.get_user_id_from_username(followedByName)
			sql = "insert into followedBy values(NULL, " + userId + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def insert_to_following_list(self, username, followingName):
		if username is None:
			self.log_error("Unexpected empty object")
			return False
		if followingName is None:
			self.log_error("Unexpected empty object")
			return False

		try:
			userId = self.get_user_id_from_username(username)
			followerId = self.get_user_id_from_username(followingName)
			sql = "insert into following values(NULL, " + userId + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def get_user_id_from_username(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return 0
		if len(username) == 0:
			self.log_error("username too short")
			return 0
		
		try:
			sql = "select id from user where username = " + self.quote_identifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return 0
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return 0

	def insert_device(self, deviceId, userId):
		if deviceStr is None:
			self.log_error("Unexpected empty object")
			return None
		if len(deviceStr) == 0:
			self.log_error("Device ID too short")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None
	
	def get_device_id_from_device_str(self, deviceStr):
		if deviceStr is None:
			self.log_error("Unexpected empty object")
			return None
		if len(deviceStr) == 0:
			self.log_error("Device ID too short")
			return None

		try:
			sql = "select id from device where device = " + self.quote_identifier(deviceStr)
			rows = self.execute(sql)
			if rows is None:
				return None
			if len(rows) == 0:
				sql = "insert into device values(NULL, " + self.quote_identifier(deviceStr) + ", 0)"
				rows = self.execute(sql)
				sql = "select id from device where device = " + self.quote_identifier(deviceStr)
				rows = self.execute(sql)
			return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def get_device_id_from_username(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		try:
			sql = "select device.id, device.device from device inner join user on device.userId=user.id and user.username = " + self.quote_identifier(username)
			rows = self.execute(sql)
			if len(rows) == 0:
				return None
			return rows[0][0],rows[0][1]
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def update_device(self, deviceId, userId):
		if deviceId is None:
			self.log_error("Unexpected empty object")
			return None
		if userId is None:
			self.log_error("Unexpected empty object")
			return None

		try:
			sql = "update device set userId = " + str(userId) + " where id = " + str(deviceId)
			rows = self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def get_latest_activity_id_for_device(self, deviceId):
		if deviceId is None:
			self.log_error("Unexpected empty object")
			return None

		try:
			sql = "select max(activityId) from location where deviceId = " + str(deviceId)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return 0

	def clear_metadata(self, deviceStr):
		if deviceStr is None:
			self.log_error("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			self.log_error("Device ID too short")
			return

		try:
			deviceId = self.get_device_id_from_device_str(deviceStr)
			if deviceId is not None:
				sql = "delete from metadata where deviceId = " + str(deviceId)
				self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def insert_metadata(self, deviceStr, activityId, dateTime, key, value):
		if deviceStr is None:
			self.log_error("Unexpected empty object")
			return
		if activityId is None:
			self.log_error("Unexpected empty object")
			return
		if key is None:
			self.log_error("Unexpected empty object")
			return
		if value is None:
			self.log_error("Unexpected empty object")
			return
		if len(deviceStr) == 0:
			self.log_error("Device ID too short")
			return
		if len(key) == 0:
			self.log_error("Metadata key too short")
			return

		try:
			if isinstance(value, str) or isinstance(value, unicode):
				valueStr = "'" + value + "'"
			else:
				valueStr = str(value)
			deviceId = self.get_device_id_from_device_str(deviceStr)
			sql = "insert into metadata values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(dateTime) + ", '" + key + "', " + valueStr + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def get_metadata(self, key, deviceId, activityId):
		if key is None:
			self.log_error("Unexpected empty object")
			return None
		if deviceId is None:
			self.log_error("Unexpected empty object")
			return None
		if activityId is None:
			self.log_error("Unexpected empty object")
			return None

		try:
			sql = "select value from metadata where key = " + self.quote_identifier(key) + " and deviceId = " + str(deviceId) + " and activityId = " + str(activityId)
			rows = self.execute(sql)
			values = []
			if rows != None:
				for row in rows:
					values.append(row[0])
			return values
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return []

	def insert_location(self, deviceStr, activityId, latitude, longitude, altitude):
		if deviceStr is None:
			self.log_error("Unexpected empty object")
			return
		if activityId is None:
			self.log_error("Unexpected empty object")
			return
		if latitude is None:
			self.log_error("Unexpected empty object")
			return
		if longitude is None:
			self.log_error("Unexpected empty object")
			return
		if altitude is None:
			self.log_error("Unexpected empty object")
			return
		try:
			deviceId = self.get_device_id_from_device_str(deviceStr)
			sql = "insert into location values(NULL, " + str(deviceId) + ", " + str(activityId) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def list_locations(self, deviceId, activityId):
		if deviceId is None:
			self.log_error("Unexpected empty object")
			return None
		if activityId is None:
			self.log_error("Unexpected empty object")
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
			self.log_error(sys.exc_info()[0])
		return locations

	def list_last_locations(self, deviceId, activityId, num):
		if deviceId is None:
			self.log_error("Unexpected empty object")
			return None
		if activityId is None:
			self.log_error("Unexpected empty object")
			return None
		if num is None:
			self.log_error("Unexpected empty object")
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
			self.log_error(sys.exc_info()[0])
		return locations

	def list_users_following(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		following = []
		
		try:
			userId = self.get_user_id_from_username(username)
			if userId != None:
				sql = "select * from following where userId = " + str(userId)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						following.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return following

	def list_users_followed_by(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		followedBy = []

		try:
			userId = self.get_user_id_from_username(username)
			if userId != None:
				sql = "select * from followedBy where userId = " + str(userId)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						followedBy.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return followedBy

