# Copyright 2017 Michael J Simms

import bcrypt
import StraenDb

MIN_PASSWORD_LEN  = 8

class UserMgr(object):
	def __init__(self, root_dir):
		self.db = StraenDb.MongoDatabase(root_dir)
		self.db.create()
		super(UserMgr, self).__init__()

	def terminate(self):
		self.db = None

	def authenticate_user(self, email, password):
		if self.db == None:
			return False, "No database."
		if len(email) == 0:
			return False, "An email address was not provided."
		if len(password) < MIN_PASSWORD_LEN:
			return False, "The password is too short."

		user_id, db_hash1, user_name = self.db.retrieve_user(email)
		if db_hash1 == None:
			return False, "The user could not be found."
		db_hash2 = bcrypt.hashpw(password.encode('utf-8'), db_hash1.encode('utf-8'))
		if db_hash1 == db_hash2:
			return True, "The user has been logged in."
		return False, "The password is invalid."

	def create_user(self, email, realname, password1, password2, device_str):
		if self.db == None:
			return False, "No database."
		if len(email) == 0:
			return False, "Email address not provided."
		if len(realname) == 0:
			return False, "Name not provided."
		if len(password1) < MIN_PASSWORD_LEN:
			return False, "The password is too short."
		if password1 != password2:
			return False, "The passwords do not match."
		if self.db.retrieve_user(email) == None:
			return False, "The user already exists."

		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(password1.encode('utf-8'), salt)
		if not self.db.create_user(email, realname, hash):
			return False, "An internal error was encountered when creating the user."

		if len(device_str) > 0:
			user_id, user_hash, user_realname = self.db.retrieve_user(email)
			self.db.create_device(device_str, user_id)
		
		return True, "The user was created."

	def list_user_devices(self, user_id):
		if self.db == None:
			return False, "No database."
		if user_id is None or len(user_id) == 0:
			return False, "Bad parameter."
		return self.db.retrieve_user_devices(user_id)

	def list_users_followed_by(self, user_id):
		if self.db == None:
			return False, "No database."
		if user_id is None or len(user_id) == 0:
			return False, "Bad parameter."
		return self.db.retrieve_users_followed_by(user_id)

	def list_users_following(self, user_id):
		if self.db == None:
			return False, "No database."
		if user_id is None or len(user_id) == 0:
			return False, "Bad parameter."
		return self.db.retrieve_users_following(user_id)

	def request_to_follow(self, email, following_name):
		if self.db == None:
			return False, "No database."
		if email is None or len(email) == 0:
			return False, "Bad parameter."
		if following_name is None or len(following_name) == 0:
			return False, "Bad parameter."

		return self.db.create_following_entry(email, followed_by_name)

	def retrieve_user(self, email):
		if self.db == None:
			return False, "No database."
		if email is None or len(email) == 0:
			return False, "Bad parameter."
		return self.db.retrieve_user(email)
