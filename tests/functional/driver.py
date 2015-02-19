import time
import slacker
import re


class Driver(object):
    """Function tests driver. It handles the communication with slack api, so that
    the tests code can concentrate on higher level logic.
    """
    def __init__(self, driver_apitoken, driver_username, testbot_username, channel):
        self.slacker = slacker.Slacker(driver_apitoken)
        self.driver_username = driver_username
        self.test_channel = channel
        self.users = {}
        self.testbot_username = testbot_username
        self.testbot_userid = None
        # public channel
        self.cm_chan = None
        # direct message channel
        self.dm_chan = None
        self._start_ts = time.time()

    def start(self):
        self._fetch_users()
        self._start_dm_channel()
        self._join_test_channel()

    def wait_for_bot_online(self):
        for _ in xrange(10):
            time.sleep(2)
            if self._is_testbot_online():
                break
        else:
            raise AssertionError('test bot is not online')

    def send_direct_message(self, msg):
        self._send_message_to_bot(self.dm_chan, msg)

    def send_channel_message(self, msg, tobot=True):
        if tobot:
            msg = '<@%s>: %s' % (self.testbot_userid, msg)
        self._send_message_to_bot(self.cm_chan, msg)

    def wait_for_bot_direct_message(self, match):
        self._wait_for_bot_message(self.dm_chan, match)

    def wait_for_bot_channel_message(self, match):
        self._wait_for_bot_message(self.cm_chan, match)

    def ensure_no_channel_reply_from_bot(self, wait=5):
        for _ in xrange(wait):
            response = self.slacker.channels.history(
                self.cm_chan, oldest=self._start_ts, latest=time.time())
            for msg in response.body['messages']:
                if self._is_bot_message(msg):
                    raise AssertionError(
                        'expected to get nothing, but got message "%s"' % msg['text'])

    def wait_for_file_uploaded(self, name, maxwait=10):
        for _ in xrange(maxwait):
            time.sleep(1)
            if self._has_uploaded_file(name):
                break
        else:
            raise AssertionError('expected to get file "%s", but got nothing' % name)

    def _send_message_to_bot(self, channel, msg):
        self._start_ts = time.time()
        self.slacker.chat.post_message(channel, msg, username=self.driver_username)

    def _wait_for_bot_message(self, channel, match, maxwait=5):
        for _ in xrange(maxwait):
            time.sleep(1)
            if self._has_got_message(channel, match):
                break
        else:
            raise AssertionError('expected to get message like "%s", but got nothing' % match)

    def _has_got_message(self, channel, match, start=None, end=None):
        oldest = start or self._start_ts
        latest = end or time.time()
        func = self.slacker.channels.history if channel.startswith('C') \
               else self.slacker.im.history
        response = func(channel, oldest=oldest, latest=latest)
        for msg in response.body['messages']:
            if msg['type'] == 'message' and re.match(match, msg['text'], re.DOTALL):
                return True
        return False

    def _fetch_users(self):
        response = self.slacker.users.list()
        for user in response.body['members']:
            self.users[user['name']] = user['id']

        self.testbot_userid = self.users[self.testbot_username]

    def _start_dm_channel(self):
        """Start a slack direct messages channel with the test bot"""
        response = self.slacker.im.open(self.testbot_userid)
        self.dm_chan = response.body['channel']['id']

    def _is_testbot_online(self):
        response = self.slacker.users.get_presence(self.testbot_userid)
        return response.body['presence'] == self.slacker.presence.ACTIVE

    def _has_uploaded_file(self, name, start=None, end=None):
        ts_from = start or self._start_ts
        ts_to = end or time.time()
        response = self.slacker.files.list(user=self.testbot_userid, ts_from=ts_from, ts_to=ts_to)
        for f in response.body['files']:
            if f['name'] == name:
                return True
        return False

    def _join_test_channel(self):
        response = self.slacker.channels.join(self.test_channel)
        self.cm_chan = response.body['channel']['id']
        self._invite_testbot_to_channel()

    def _invite_testbot_to_channel(self):
        if self.testbot_userid not in self.slacker.channels.info(self.cm_chan).body['channel']['members']:
            self.slacker.channels.invite(self.cm_chan, self.testbot_userid)

    def _is_bot_message(self, msg):
        if msg['type'] != 'message':
            return False
        return msg.get('user') == self.testbot_userid \
            or msg.get('username') == self.testbot_username
