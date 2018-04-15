# Copyright 2017 Michael J Simms
import argparse
import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import Importer

class TestLocationWriter(Importer.LocationWriter):
    """Subclass that implements the location writer and will receive the locations as they are read from the file."""

    def create_location_stream(self, username):
        return None, None

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        print device_str, activity_id, date_time, latitude, longitude, altitude


if __name__ == "__main__":

    successes = []
    failures = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory of files to be processed", required=True)
    args = parser.parse_args()

    store = TestLocationWriter()
    importer = Importer.Importer(store)

    for subdir, dirs, files in os.walk(args.dir):
        for current_file in files:
            full_path = os.path.join(subdir, current_file)
            temp_file_name, temp_file_ext = os.path.splitext(full_path)
            if importer.import_file("test user", full_path, temp_file_ext):
                successes.append(current_file)
            else:
                failures.append(current_file)

    print "Num success: " + str(len(successes))
    print "Num failures: " + str(len(failures))