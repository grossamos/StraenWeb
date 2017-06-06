# Copyright 2017 Michael J Simms

from bson.objectid import ObjectId

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
			user = self.users_collection.find_one({"username": username})
			if user is not None:
				return str(user['_id']), user['hash'], user['realname']
			return None, None, None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None, None, None

	def retrieve_user_activities(self, user_id):
		if user_id is None:
			self.log_error(MongoDatabase.retrieve_user_activities.__name__ + "Unexpected empty object: user_id")
			return None

		try:
			user_id_obj = ObjectId(user_id)
			user = self.users_collection.find_one({"_id": user_id_obj})
			if user is not None:
				return user['activities']
		except KeyError:
			return None
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_user_devices(self, user_id):
		if user_id is None:
			self.log_error(MongoDatabase.retrieve_user_devices.__name__ + "Unexpected empty object: user_id")
			return None

		try:
			user_id_obj = ObjectId(user_id)
			user = self.users_collection.find_one({"_id": user_id_obj})
			if user is not None:
				return user['devices']
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_users_following(self, user_id):
		if user_id is None:
			self.log_error(MongoDatabase.retrieve_users_following.__name__ + "Unexpected empty object: user_id")
			return None

		try:
			user_id_obj = ObjectId(user_id)
			user = self.users_collection.find_one({"_id": user_id_obj})
			if user is not None:
				return users['following']
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_users_followed_by(self, user_id):
		if user_id is None:
			self.log_error(MongoDatabase.retrieve_users_followed_by.__name__ + "Unexpected empty object: user_id")
			return None

		try:
			pass
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def create_following_entry(self, user_id, following_name):
		if user_id is None:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: user_id")
			return None
		if following_name is None:
			self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: following_name")
			return False

		try:
			user_id_obj = ObjectId(user_id)
			user = self.users_collection.find_one({"_id": user_id_obj})
			if user is not None:
				list = user['following']
				if following_name not in list:
					list.append(following_name)
					user['following'] = list
					self.users_collection.save(user)
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
			user_id_obj = ObjectId(user_id)
			user = self.users_collection.find_one({"_id": user_id_obj})
			if user is not None:
				list = user['devices']
				if device_str not in list:
					list.append(device_str)
					user['devices'] = list
					self.users_collection.save(user)
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return False

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

	def create_activity(self, activity_id, activty_name, device_str):
		if activity_id is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activity_id")
			return False
		if activty_name is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activty_name")
			return False
		if device_str is None:
			self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: device_str")
			return False

		try:
			post = {"activity_id": str(activity_id), "activty_name": activty_name, "device_str": device_str, "locations": []}
			self.activities_collection.insert(post)
			return True
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
			activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
			if len(activity) == 0:
				if self.create_activity(activity_id, "", device_str):
					activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
			if len(activity) > 0:
				activity[key] = value
				self.activities_collection.save(activity)
				return True
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
			activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
			if len(activity) == 0:
				if self.create_activity(activity_id, "", device_str):
					activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
			if len(activity) > 0:
				data = activity[sensor_type]
				data.append({date_time, value})
				self.activities_collection.save(activity)
				return True
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
			activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
			if activity is None:
				sensor_data = activity[sensor_type]
				return sensor_data
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
			activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
			if activity is None:
				if self.create_activity(activity_id, "", device_str):
					activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
			if activity is None:
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
			activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
			if activity is not None:
				locations = activity['locations']
				return locations
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None

	def retrieve_most_recent_locations(self, device_str, activity_id, num):
		if num is None:
			self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + "Unexpected empty object: num")
			return None

		try:
			locations = self.retrieve_locations(device_str, activity_id)
			return locations
		except:
			traceback.print_exc(file=sys.stdout)
			self.log_error(sys.exc_info()[0])
		return None
