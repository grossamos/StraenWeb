# Copyright 2017 Michael J Simms

class StraenApi(object):
    def __init__(self):
        super(StraenApi, self).__init__()

    def handle_api_1_0_request(self, args):
        if len(args) > 0:
            request = args[0]
            if request == 'upload':
                pass
            elif request == 'add_tag':
                pass
            elif request == 'delete_tag':
                pass
                