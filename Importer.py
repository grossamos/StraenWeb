# Copyright 2017 Michael J Simms

import calendar
import datetime
import gpxpy

class LocationWriter(object):
    """Base class for any class that handles data read from the Importer."""

    def create_location_stream(self, username):
        """Pure virtual method for starting a location stream - creates the activity ID for the specified user."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Pure virtual method for processing a location read by the importer."""
        pass

class Importer(object):
    """Importer for GPX and TCX location files."""
    def __init__(self, location_store):
        super(Importer, self).__init__()
        self.g_location_store = location_store

    def import_gpx_file(self, username, file_name):
        """Imports the specified GPX file."""
        with open(file_name, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            device_str, activity_id = self.g_location_store.create_location_stream(username)

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        dt_str = str(point.time) + " UTC"
                        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %Z").timetuple()
                        dt_unix = calendar.timegm(dt_obj)
                        self.g_location_store.create_location(device_str, activity_id, dt_unix, point.latitude, point.longitude, point.elevation)

            return True
        return False

    def import_tcx_file(self, username, file_name):
        """Imports the specified TCX file."""
        tcx = tcxparser.TCXParser(file_name)
        if tcx is not None:
            return True
        return False

    def import_file(self, username, local_file_name, file_extension):
        """Imports the specified file, parsing it based on the provided extension."""
        try:
            if file_extension == '.gpx':
                return self.import_gpx_file(username, local_file_name)
            elif file_extension == '.tcx':
                return self.import_gpx_file(username, local_file_name)
        except:
            pass
        return False
