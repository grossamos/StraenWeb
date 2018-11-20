# Copyright 2017 Michael J Simms
"""Key strings for all key/value pairs used in the app"""

# Keys associated with user management.
SESSION_KEY = '_straen_username'
DATABASE_ID_KEY = "_id"
USERNAME_KEY = "username"
PASSWORD_KEY = "password"
PASSWORD1_KEY = "password1"
PASSWORD2_KEY = "password2"
DEVICE_KEY = "device"
REALNAME_KEY = "realname"
HASH_KEY = "hash"
DEVICES_KEY = "devices"
FOLLOWING_KEY = "following"
PR_KEY = "pr"

# User settings
DEFAULT_PRIVACY = "default privacy"

# Keys inherited from the mobile app.
APP_NAME_KEY = "Name"
APP_TIME_KEY = "Time"
APP_USERNAME_KEY = "User Name"
APP_DEVICE_ID_KEY = "DeviceId"
APP_ID_KEY = "ActivityId"
APP_TYPE_KEY = "ActivityType"
APP_DISTANCE_KEY = "Distance"
APP_CADENCE_KEY = "Cadence"
APP_TEMP_KEY = "Temperature"
APP_CURRENT_SPEED_KEY = "Current Speed"
APP_AVG_SPEED_KEY = "Avgerage Speed"
APP_MOVING_SPEED_KEY = "Moving Speed"
APP_HEART_RATE_KEY = "Heart Rate"
APP_AVG_HEART_RATE_KEY = "Average Heart Rate"
APP_CURRENT_PACE_KEY = "Current Pace"
APP_POWER_KEY = "Power"
APP_SETS_KEY = "Sets"
APP_LOCATIONS_KEY = "locations"
APP_LOCATION_LAT_KEY = "Latitude"
APP_LOCATION_LON_KEY = "Longitude"
APP_LOCATION_ALT_KEY = "Altitude"
APP_ACCELEROMETER_KEY = "accelerometer"
APP_AXIS_NAME_X = "x"
APP_AXIS_NAME_Y = "y"
APP_AXIS_NAME_Z = "z"

LOCATION_LAT_KEY = "latitude"
LOCATION_LON_KEY = "longitude"
LOCATION_ALT_KEY = "altitude"
LOCATION_TIME_KEY = "time"

ACCELEROMETER_AXIS_NAME_X = "x"
ACCELEROMETER_AXIS_NAME_Y = "y"
ACCELEROMETER_AXIS_NAME_Z = "z"
ACCELEROMETER_TIME_KEY = "time"

# Keys used exclusively by the web app.
ACTIVITY_ID_KEY = "activity_id"
ACTIVITY_TYPE_KEY = "activity_type"
ACTIVITY_DEVICE_STR_KEY = "device_str"
ACTIVITY_LOCATIONS_KEY = "locations"
ACTIVITY_NAME_KEY = "name"
ACTIVITY_TIME_KEY = "time"
ACTIVITY_VISIBILITY_KEY = "visibility"
ACTIVITY_VISIBILITY_PUBLIC = "public"
ACTIVITY_VISIBILITY_PRIVATE = "private"
ACTIVITY_COMMENT_KEY = "comment"
ACTIVITY_COMMENTS_KEY = "comments"
ACTIVITY_COMMENTER_ID_KEY = "commenter_id"
ACTIVITY_TAGS_KEY = "tags"
ACTIVITY_SUMMARY_KEY = "summary_data"

# Keys used to summarize activity data.
BEST_SPEED = "Best Speed"
BEST_1K = "Best 1K"
BEST_MILE = "Best Mile"
BEST_5K = "Best 5K"
BEST_10K = "Best 10K"
BEST_15K = "Best 15K"
BEST_HALF_MARATHON = "Best Half Marathon"
BEST_MARATHON = "Best Marathon"
BEST_METRIC_CENTURY = "Best Metric Century"
BEST_CENTURY = "Best Century"
BEST_5_SEC_POWER = "5 Second Power"
BEST_20_MIN_POWER = "20 Minute Power"
BEST_1_HOUR_POWER = "1 Hour Power"
MAX_POWER = "Maximum Power"
MAX_HEART_RATE = "Maximum Heart Rate"
MAX_CADENCE = "Maximum Cadence"
AVG_POWER = "Average Power"
AVG_HEART_RATE = "Average Heart Rate"
AVG_CADENCE = "Average Cadence"
NORMALIZED_POWER = "Normalized Power"
CLUSTER = 'Cluster'

# Activity types
TYPE_RUNNING_KEY = "Running"
TYPE_CYCLING_KEY = "Cycling"
TYPE_SWIMMING_KEY = "Swimming"
TYPE_PULL_UPS_KEY = "Pull Ups"
