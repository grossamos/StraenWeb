# Copyright 2017 Michael J Simms

import StraenDb

class DataMgr(object):
	def __init__(self, root_dir):
		self.db = StraenDb.MongoDatabase(root_dir)
		self.db.create()
		super(DataMgr, self).__init__()

	def terminate(self):
		self.db = None

	def retrieve_user_activities(self, user_id):
		if self.db == None:
			return False, "No database."
		if username is None or len(username) == 0:
			return False, "Bad parameter."
		return self.retrieve_user_activities(user_id)

	def retrieve_locations(self, device_str, activity_id):
		if self.db == None:
			return False, "No database."
		if device_str is None or len(device_str) == 0:
			return False, "Bad parameter."
		if activity_id is None:
			return False, "Bad parameter."
		return self.db.retrieve_locations(device_str, activity_id)

	def retrieve_metadata(self, key, device_str, activity_id):
		if self.db == None:
			return False, "No database."
		if device_str is None or len(device_str) == 0:
			return False, "Bad parameter."
		if activity_id is None:
			return False, "Bad parameter."
		return self.db.retrieve_metadata(key, device_str, activity_id)

	def retrieve_sensordata(self, key, device_str, activity_id):
		if self.db == None:
			return False, "No database."
		if device_str is None or len(device_str) == 0:
			return False, "Bad parameter."
		if activity_id is None:
			return False, "Bad parameter."
		return self.db.retrieve_sensordata(key, device_str, activity_id)

	def retrieve_most_recent_locations(self, device_str, activity_id, num):
		if self.db == None:
			return False, "No database."
		if device_str is None or len(device_str) == 0:
			return False, "Bad parameter."
		if activity_id is None:
			return False, "Bad parameter."
		return self.db.retrieve_most_recent_locations(device_str, activity_id, num)
