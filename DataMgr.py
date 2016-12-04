import bcrypt
import ExertDb

class DataMgr(object):
	def __init__(self, root_dir):
		self.db = ExertDb.ExertSqlDb(root_dir)
		super(DataMgr, self).__init__()

	def terminate(self):
		self.db = None

	def authenticate_user(self, email, password):
		if len(email) == 0:
			return False, "An email address was not provided."
		if len(password) < MIN_PASSWORD_LEN:
			return False, ""

		db_hash = self.db.retrieve_user_hash(email)
		if db_hash == 0:
			return False, "The user could not be found."
		if db_hash == bcrypt.hashpw(password, db_hash):
			logged_in = True
			auth_str = "The user has been logged in."
		else:
			logged_in = False
			auth_str = "The password is invalid."
		return logged_in, auth_str

	def create_user(self, email, realname, password1, password2, device_str):
		if len(email) == 0:
			return False, "Email address not provided."
		if len(realname) == 0:
			return False, "Name not provided."
		if len(password1) < MIN_PASSWORD_LEN:
			return False, "The password is too short."
		if password1 != password2:
			return False, "The passwords do not match."
		if self.db.retrieve_user_hash(email) != 0:
			return False, "The user already exists."

		salt = bcrypt.gensalt()
		hash = bcrypt.hashpw(password1, salt)
		if not self.db.create_user(email, realname, hash):
			return False, ""

		user_id = self.db.retrieve_user_id_from_username(email)

		if len(device_str) > 0:
			device_id = self.db.retrieve_device_id_from_device_str(device_str)
			self.db.update_device(device_id, user_id)
		
		return True, "The user was created."

	def list_users_followed_by(self, email):
		return self.db.retrieve_users_followed_by(email)

	def list_users_following(self, email):
		return self.db.retrieve_users_following(email)

	def invite_to_follow(self, email, followed_by_name):
		if len(email) == 0:
			return False
		if len(followed_by_name) == 0:
			return False

		return self.db.create_followed_by_entry(email, followed_by_name)

	def request_to_follow(self, email, following_name):
		if len(email) == 0:
			return False
		if len(following_name) == 0:
			return False

		return self.db.create_following_entry(email, followed_by_name)

