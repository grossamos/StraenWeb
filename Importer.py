# Copyright 2017 Michael J Simms

import gpxpy
import tcxparser

class Importer(object):
    def __init__(self, data_mgr):
        super(Importer, self).__init__()
        g_data_mgr = data_mgr

    def import_gpx_file(self, username, file_name):
        with open(file_name, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        dt_str = point.time + " UTC"
                        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").timetuple()
                        dt_unix = calendar.timegm(foo.utctimetuple())

                        //self.g_data_mgr.create_location(device_str, activity_id, dt_unix, point.latitude, point.longitude, point.elevation)

            return True
        return False

    def import_tcx_file(self, username, file_name):
        tcx = tcxparser.TCXParser(file_name)
        if tcx is not None:
            return True
        return False

    def import_file(self, username, local_file_name, file_extension):
        try:
            if file_extension == '.gpx':
                return self.import_gpx_file(username, local_file_name)
            elif file_extension == '.tcx':
                return self.import_gpx_file(username, local_file_name)
        except:
            pass
        return False
