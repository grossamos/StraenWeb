import os
import sqlite3
import sys
import traceback

class Location(object):
	def __init__(self):
		self.latitude = 0.0
		self.longitude = 0.0
		super(Location, self).__init__()

class Device(object):
	def __init__(self):
		self.id = 0
		self.name = ""
		self.description = ""
		super(Device, self).__init__()

class Database(object):
	db_file = ""
	
	def __init__(self, root_dir):
		self.db_file = os.path.join(root_dir, 'exert.sqlite')
		self.log_file_name = os.path.join(root_dir, 'ExertDb.log')
		super(Database, self).__init__()
	
	def log_error(self, log_str):
		with open(self.log_file_name, 'a') as f:
			f.write(str(log_str) + "\n")
			f.close()

class MysqlDatabase(Database):
	def __init__(self, rootDir):
		Database.__init__(self, rootDir)
	
	def connect(self):
		pass

	def execute(self, sql):
		pass

class SqliteDatabase(Database):
	def __init__(self, rootDir):
		Database.__init__(self, rootDir)

	def connect(self):
		pass

	def execute(self, sql):
		try:
			con = sqlite3.connect(self.db_file)
			with con:
				cur = con.cursor()
				cur.execute(sql)
				return cur.fetchall()
		except:
			self.log_error("Database error:\n\tfile = " + self.db_file + "\n\tsql = " + self.quote_identifier(sql))
		finally:
			if con:
				con.close()
		return None

class ExertDb(SqliteDatabase):
	def __init__(self, rootDir):
		SqliteDatabase.__init__(self, rootDir)

	def quote_identifier(self, s, errors="strict"):
		encodable = s.encode("utf-8", errors).decode("utf-8")
		null_index = encodable.find("\x00")
		if null_index >= 0:
			return ""
		return "\"" + encodable.replace("\"", "\"\"") + "\""

	def create(self):
		try:
			self.execute("create table activity (id integer primary key, name text, activityType integer)")
		except:
			pass

		try:
			self.execute("create table location (id integer primary key, deviceId integer, activityId integer, latitude double, longitude double, altitude double)")
		except:
			pass

		try:
			self.execute("create table metadata (id integer primary key, deviceId integer, activityId integer, time integer, key text, value double)")
		except:
			pass

		try:
			self.execute("create table sensordata (id integer primary key, deviceId integer, activityId integer, time integer, sensorType integer, value double)")
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
			self.execute("create table device (id integer primary key, device text, userId integer, public integer)")
		except:
			pass
	
	def create_user(self, username, realname, hash):
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

	def retrieve_user_hash(self, username):
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

	def retrieve_user_id_from_username(self, username):
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

	def retrieve_realname_from_username(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return ""
		if len(username) == 0:
			self.log_error("username too short")
			return ""
		
		try:
			sql = "select realname from user where username = " + self.quote_identifier(username)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
			return ""
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return ""

	def create_followed_by_entry(self, username, followed_by_name):
		if username is None:
			self.log_error("Unexpected empty object")
			return False
		if followed_by_name is None:
			self.log_error("Unexpected empty object")
			return False

		try:
			user_id = self.retrieve_user_id_from_username(username)
			followerId = self.retrieve_user_id_from_username(followed_by_name)
			sql = "insert into followedBy values(NULL, " + user_id + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def create_following_entry(self, username, following_name):
		if username is None:
			self.log_error("Unexpected empty object")
			return False
		if following_name is None:
			self.log_error("Unexpected empty object")
			return False

		try:
			user_id = self.retrieve_user_id_from_username(username)
			followerId = self.retrieve_user_id_from_username(following_name)
			sql = "insert into following values(NULL, " + user_id + ", " + followerId + ", 0)"
			rows = self.execute(sql)
			return rows != None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def create_device(self, device_str, user_id):
		if device_str is None:
			self.log_error("Unexpected empty object")
			return None
		if len(device_str) == 0:
			self.log_error("Device ID too short")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None
	
	def retrieve_device_id_from_device_str(self, device_str):
		if device_str is None:
			self.log_error("Unexpected empty object")
			return None
		if len(device_str) == 0:
			self.log_error("Device ID too short")
			return None

		try:
			sql = "select id from device where device = " + self.quote_identifier(device_str)
			rows = self.execute(sql)
			if rows is None or len(rows) == 0:
				sql = "insert into device values(NULL, " + self.quote_identifier(device_str) + ", 0)"
				rows = self.execute(sql)
				sql = "select id from device where device = " + self.quote_identifier(device_str)
				rows = self.execute(sql)
			return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_device_ids_for_username(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		devices = []

		try:
			sql = "select device.id, device.device from device inner join user on device.userId=user.id and user.username = " + self.quote_identifier(username)
			rows = self.execute(sql)
			if rows != None:
				for row in rows:
					device = Location()
					device.id = rows[0][0]
					device.name = rows[0][1]
					devices.append(location)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return devices

	def retrieve_most_recent_activity_id_for_device(self, device_id):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		
		try:
			sql = "select max(activityId) from location where deviceId = " + str(device_id)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				return rows[0][0]
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return 0

	def update_device(self, device_id, user_id):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		if user_id is None:
			self.log_error("Unexpected empty object")
			return None

		try:
			sql = "update device set userId = " + str(user_id) + " where id = " + str(device_id)
			rows = self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def clear_metadata_for_device(self, device_id):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return

		try:
			if device_id is not None:
				sql = "delete from metadata where deviceId = " + str(device_id)
				self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def clear_metadata_for_activity(self, device_id, activity_id):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return
	
		try:
			if device_id is not None:
				sql = "delete from metadata where deviceId = " + str(device_id) + " and activityId = " + str(activity_id)
				self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def create_metadata(self, device_id, activity_id, date_time, key, value):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return
		if date_time is None:
			self.log_error("Unexpected empty object")
			return
		if key is None:
			self.log_error("Unexpected empty object")
			return
		if value is None:
			self.log_error("Unexpected empty object")
			return
		if len(key) == 0:
			self.log_error("Metadata key too short")
			return

		try:
			if isinstance(value, str) or isinstance(value, unicode):
				valueStr = "'" + value + "'"
			else:
				valueStr = str(value)
			sql = "insert into metadata values(NULL, " + str(device_id) + ", " + str(activity_id) + ", " + str(date_time) + ", '" + key + "', " + valueStr + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def retrieve_metadata(self, key, device_id, activity_id):
		if key is None:
			self.log_error("Unexpected empty object")
			return None
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return None

		try:
			sql = "select time,value from metadata where key = " + self.quote_identifier(key) + " and deviceId = " + str(device_id) + " and activityId = " + str(activity_id)
			return self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return []

	def create_sensordata(self, device_id, activity_id, date_time, sensor_type, value):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return
		if date_time is None:
			self.log_error("Unexpected empty object")
			return
		if sensor_type is None:
			self.log_error("Unexpected empty object")
			return
		if value is None:
			self.log_error("Unexpected empty object")
			return

		try:
			sql = "insert into sensordata values(NULL, " + str(device_id) + ", " + str(activity_id) + ", " + str(date_time) + ", " + str(sensor_type) + ", " + str(value) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return
	
	def retrieve_sensordata(self, sensor_type, device_id, activity_id):
		if sensor_type is None:
			self.log_error("Unexpected empty object")
			return None
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return None
		
		try:
			sql = "select time,value from sensordata where sensorType = " + str(sensor_type) + " and deviceId = " + str(device_id) + " and activityId = " + str(activity_id)
			return self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return []

	def create_location(self, device_id, activity_id, latitude, longitude, altitude):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return
		if activity_id is None:
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
			sql = "insert into location values(NULL, " + str(device_id) + ", " + str(activity_id) + ", " + str(latitude) + ", " + str(longitude) + ", " + str(altitude) + ")"
			self.execute(sql)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return

	def retrieve_locations(self, device_id, activity_id):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select latitude, longitude from location where deviceId = " + str(device_id) + " and activityId = " + str(activity_id)
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

	def retrieve_most_recent_locations(self, device_id, activity_id, num):
		if device_id is None:
			self.log_error("Unexpected empty object")
			return None
		if activity_id is None:
			self.log_error("Unexpected empty object")
			return None
		if num is None:
			self.log_error("Unexpected empty object")
			return None

		locations = []

		try:
			sql = "select count(*) from location where deviceId = " + str(device_id) + " and activityId = " + str(activity_id)
			rows = self.execute(sql)
			if rows != None and len(rows) > 0:
				rowCount = int(rows[0][0])
				newRows = rowCount - num
				if newRows > 0:
					sql = "select latitude, longitude from location where deviceId = " + str(device_id) + " and activityId = " + str(activity_id) + " order by id desc limit " + str(num)
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

	def retrieve_users_following(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		following = []
		
		try:
			user_id = self.retrieve_user_id_from_username(username)
			if user_id != None:
				sql = "select * from following where userId = " + str(user_id)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						following.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return following

	def retrieve_users_followed_by(self, username):
		if username is None:
			self.log_error("Unexpected empty object")
			return None
		if len(username) == 0:
			self.log_error("username too short")
			return None

		followedBy = []

		try:
			user_id = self.retrieve_user_id_from_username(username)
			if user_id != None:
				sql = "select * from followedBy where userId = " + str(user_id)
				rows = self.execute(sql)
				if rows != None:
					for row in rows:
						followedBy.append(row[0])
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return followedBy

