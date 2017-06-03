# Copyright 2017 Michael J Simms

import os
import pymongo
import sqlite3
import sys
import traceback
import Database

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

class MongoDatabase(Database.Database):
	conn = None
	db = None
	users_collection = None
	activities_collection = None

	def __init__(self, rootDir):
		Database.Database.__init__(self, rootDir)
		self.create()

	def create(self):
		try:
			self.conn = pymongo.MongoClient('localhost:27017')
			self.db = self.conn['straendb']
			self.users_collection = self.db['users']
			self.activities_collection = self.db['activities']
			return True
		except pymongo.errors.ConnectionFailure, e:
			self.log_error("Could not connect to MongoDB: %s" % e)
		return False

	def create_user(self, username, realname, hash):
		if username is None:
			self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: username")
			return False
		if realname is None:
			self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: realname")
			return False
		if hash is None:
			self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: hash")
			return False
		if len(username) == 0:
			self.log_error(MongoDatabase.create_user.__name__ + "username too short")
			return False
		if len(realname) == 0:
			self.log_error(MongoDatabase.create_user.__name__ + "realname too short")
			return False
		if len(hash) == 0:
			self.log_error(MongoDatabase.create_user.__name__ + "hash too short")
			return False

		try:
			post = {"username": username, "realname": realname, "hash": hash, "devices": [], "following": []}
			self.users_collection.insert(post)
			return True
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_user(self, username):
		if username is None:
			self.log_error(MongoDatabase.retrieve_user.__name__ + "Unexpected empty object: username")
			return None, None, None
		if len(username) == 0:
			self.log_error(MongoDatabase.retrieve_user.__name__ + "username is empty")
			return None, None, None

		try:
			users = self.users_collection.find_one({"username": username})
			if len(users) > 0:
				return str(users['_id']), users['hash'], users['realname']
			return None, None, None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None, None, None

	def retrieve_user_activities(self, user_id):
		if user_id is None:
			self.log_error(MongoDatabase.retrieve_user_activities.__name__ + "Unexpected empty object: username")
			return None
		if len(user_id) == 0:
			self.log_error(MongoDatabase.retrieve_user_activities.__name__ + "username is empty")
			return None

		try:
			users = self.users_collection.find_one({"_id": user_id})
			if len(users) > 0:
				return str(users['activities'])
			return None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_following_entry(self, username, following_name):
		if username is None:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: username")
			return False
		if len(username) == 0:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "username is empty")
			return False
		if following_name is None:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: following_name")
			return False
		if len(following_name) == 0:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "following_name is empty")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def create_device(self, device_str, user_id):
		if device_str is None:
			self.log_error(MongoDatabase.create_device.__name__ + "Unexpected empty object: device_str")
			return False
		if user_id is None:
			self.log_error(MongoDatabase.create_device.__name__ + "Unexpected empty object: user_id")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_device_strs_for_username(self, username):
		devices = []

		if username is None:
			self.log_error(MongoDatabase.retrieve_device_strs_for_username.__name__ + "Unexpected empty object: username")
			return devices
		if len(username) == 0:
			self.log_error(MongoDatabase.retrieve_device_strs_for_username.__name__ + "username too short")
			return devices
		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return devices

	def retrieve_most_recent_activity_id_for_device(self, device_str):
		if device_str is None:
			self.log_error(MongoDatabase.retrieve_most_recent_activity_id_for_device.__name__ + "Unexpected empty object: device_str")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_device(self, device_str, user_id):
		if device_str is None:
			self.log_error(MongoDatabase.create_device.__name__ + "Unexpected empty object: device_str")
			return False
		if user_id is None:
			self.log_error(MongoDatabase.create_device.__name__ + "Unexpected empty object: user_id")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def create_metadata(self, device_str, activity_id, date_time, key, value):
		if device_str is None:
			self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: device_str")
			return False
		if activity_id is None:
			self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: activity_id")
			return False
		if date_time is None:
			self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: date_time")
			return False
		if key is None:
			self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: key")
			return False
		if value is None:
			self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: value")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_metadata(self, key, device_str, activity_id):
		if device_str is None:
			self.log_error(MongoDatabase.retrieve_metadata.__name__ + "Unexpected empty object: device_str")
			return None
		if activity_id is None:
			self.log_error(MongoDatabase.retrieve_metadata.__name__ + "Unexpected empty object: activity_id")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_sensordata(self, device_str, activity_id, date_time, sensor_type, value):
		if device_str is None:
			self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: device_str")
			return False
		if activity_id is None:
			self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: activity_id")
			return False
		if date_time is None:
			self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: date_time")
			return False
		if sensor_type is None:
			self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: sensor_type")
			return False
		if value is None:
			self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: value")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_sensordata(self, sensor_type, device_str, activity_id):
		if sensor_type is None:
			self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: sensor_type")
			return None
		if device_str is None:
			self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: device_str")
			return None
		if activity_id is None:
			self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: activity_id")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_location(self, device_str, activity_id, latitude, longitude, altitude):
		if device_str is None:
			self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: device_str")
			return False
		if activity_id is None:
			self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: activity_id")
			return False
		if latitude is None:
			self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: latitude")
			return False
		if longitude is None:
			self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: longitude")
			return False
		if altitude is None:
			self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: altitude")
			return False

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_locations(self, device_str, activity_id):
		if device_str is None:
			self.log_error(MongoDatabase.retrieve_locations.__name__ + "Unexpected empty object: device_str")
			return None
		if activity_id is None:
			self.log_error(MongoDatabase.retrieve_locations.__name__ + "Unexpected empty object: activity_id")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_most_recent_locations(self, device_str, activity_id, num):
		if device_str is None:
			self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + "Unexpected empty object: device_str")
			return None
		if activity_id is None:
			self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + "Unexpected empty object: activity_id")
			return None
		if num is None:
			self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + "Unexpected empty object: num")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_activity(self, activity_id, activty_name, device_str):
		if device_str is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: device_str")
			return False
		if activity_id is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activity_id")
			return False
		if activty_name is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activty_name")
			return False

		try:
			post = {"activity_id": activity_id, "activty_name": activty_name, "device_str": device_str, "locations": []}
			self.activities_collection.insert(post)
			return True
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

	def retrieve_users_following(self, username):
		if username is None:
			self.log_error(retrieve_users_following.__name__ + "Unexpected empty object: username")
			return None
		if len(username) == 0:
			self.log_error(retrieve_users_following.__name__ + "username is empty")
			return None

		try:
			users = self.users_collection.find_one({"username": username})
			if len(users) > 0:
				return users['following']
			return None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_users_followed_by(self, username):
		if username is None:
			self.log_error(retrieve_users_followed_by.__name__ + "Unexpected empty object: username")
			return None
		if len(username) == 0:
			self.log_error(retrieve_users_followed_by.__name__ + "username is empty")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None
