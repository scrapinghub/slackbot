import slacker
from collections import namedtuple

class RTMClient(object):
    def connect(self):
        pass

    def get_events(self):
        pass

    def send_message(self, channel, msg):
        pass

UploadFileInfo = namedtuple('UploadFileInfo', [
    'filepath',
    'filename',
    'initial_comment',
])

class WebApiClient(object):
    def __init__(self, token):
        self.slacker = slacker.Slacker(token)

    def upload_file(self, channel_id, uploadfileinfo):
        u = uploadfileinfo
        self.slacker.files.upload(u.filepath,
                                  channels=channel_id,
                                  filename=u.filename,
                                  initial_comment=u.initial_comment)

