import os
from slack.utils import to_utf8

class Channel(object):
    def __init__(self, server, name, id, members=None):
        self.server = server
        self.name = name
        self.id = id
        self.members = members or []

    def __eq__(self, compare_str):
        if self.name == compare_str or self.id == compare_str:
            return True
        else:
            return False

    def __str__(self):
        data = ""
        for key in self.__dict__.keys():
            data += "{0} : {1}\n".format(key, str(self.__dict__[key])[:40])
        return data

    def __repr__(self):
        return self.__str__()

    def send_message(self, message):
        message_json = {"type": "message", "channel": self.id, "text": message}
        self.server.send_to_websocket(message_json)

    def upload_file(self, fname, fpath, comment):
        fname = fname or to_utf8(os.path.basename(fpath))
        self.server.slackapi.files.upload(fpath,
                                          channels=self.id,
                                          filename=fname,
                                          initial_comment=comment)
