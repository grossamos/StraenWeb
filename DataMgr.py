# Copyright 2017 Michael J Simms

import StraenDb

class DataMgr(object):
	def __init__(self, root_dir):
		self.db = StraenDb.MongoDatabase(root_dir)
		self.db.create()
		super(DataMgr, self).__init__()

	def terminate(self):
		self.db = None

	def retrieve_locations(self, deviceStr, activityId):
		if self.db == None:
			return False, "No database."
		if len(deviceStr) == 0:
			return False
		return self.db.retrieve_locations(deviceStr, activityId)

	def retrieve_metadata(self, key, deviceStr, activityId):
		if self.db == None:
			return False, "No database."
		if len(deviceStr) == 0:
			return False
		return self.db.retrieve_metadata(key, deviceStr, activityId)

	def retrieve_sensordata(self, key, deviceStr, activityId):
		if self.db == None:
			return False, "No database."
		if len(deviceStr) == 0:
			return False
		return self.db.retrieve_sensordata(key, deviceStr, activityId)

	def retrieve_most_recent_locations(self, deviceStr, activityId, num):
		if self.db == None:
			return False, "No database."
		if len(deviceStr) == 0:
			return False
		return self.db.retrieve_most_recent_locations(deviceStr, activityId, num)
