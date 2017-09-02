# Copyright 2017 Michael J Simms

import StraenDb


class DataMgr(object):
    def __init__(self, root_dir):
        self.db = StraenDb.MongoDatabase(root_dir)
        self.db.create()
        super(DataMgr, self).__init__()

    def terminate(self):
        self.db = None

    def retrieve_user_activities(self, user_id, start, num_results):
        if self.db is None:
            return None, "No database."
        if user_id is None or len(user_id) == 0:
            return None, "Bad parameter."

        activities = []
        devices = self.db.retrieve_user_devices(user_id)
        if devices is not None:
            for device in devices:
                device_activities = self.db.retrieve_device_activities(device, start, num_results)
                activities.extend(device_activities)
        return activities

    def retrieve_activity_visibility(self, device_str, activity_id):
        if self.db is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.db.retrieve_activity_visibility(device_str, activity_id)

    def update_activity_visibility(self, device_str, activity_id, visibility):
        if self.db is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        if visibility is None:
            return None, "Bad parameter."
        return self.db.update_activity_visibility(device_str, activity_id, visibility)

    def retrieve_locations(self, device_str, activity_id):
        if self.db is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.db.retrieve_locations(device_str, activity_id)

    def retrieve_metadata(self, key, device_str, activity_id):
        if self.db is None:
            return None, "No database."
        if key is None or len(key) == 0:
            return None, "Bad parameter."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.db.retrieve_metadata(key, device_str, activity_id)

    def retrieve_sensordata(self, key, device_str, activity_id):
        if self.db is None:
            return None, "No database."
        if key is None or len(key) == 0:
            return None, "Bad parameter."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.db.retrieve_sensordata(key, device_str, activity_id)

    def retrieve_most_recent_locations(self, device_str, activity_id, num):
        if self.db is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.db.retrieve_most_recent_locations(device_str, activity_id, num)

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        if self.db is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        return self.db.retrieve_most_recent_activity_id_for_device(device_str)
