import thread
import threading
import json
import re
import time
import slacker
import websocket


class Driver(object):
    """Functional tests driver. It handles the communication with slack api, so that
    the tests code can concentrate on higher level logic.
    """
    def __init__(self, driver_apitoken, driver_username, testbot_username, channel, group):
        self.slacker = slacker.Slacker(driver_apitoken)
        self.driver_username = driver_username
        self.driver_userid = None
        self.test_channel = channel
        self.test_group = group
        self.users = {}
        self.testbot_username = testbot_username
        self.testbot_userid = None
        # public channel
        self.cm_chan = None
        # direct message channel
        self.dm_chan = None
        # private group channel
        self.gm_chan = None
        self._start_ts = time.time()
        self._websocket = None
        self.events = []
        self._events_lock = threading.Lock()

    def start(self):
        self._rtm_connect()
        # self._fetch_users()
        self._start_dm_channel()
        self._join_test_channel()

    def wait_for_bot_online(self):
        self._wait_for_bot_presense(True)

    def wait_for_bot_offline(self):
        self._wait_for_bot_presense(False)

    def _wait_for_bot_presense(self, online):
        for _ in xrange(10):
            time.sleep(2)
            if online and self._is_testbot_online():
                break
            if not online and not self._is_testbot_online():
                break
        else:
            raise AssertionError('test bot is still %s' % ('offline' if online else 'online'))

    def _format_message(self, msg, tobot=True, colon=True):
        colon = ':' if colon else ''
        if tobot:
            msg = '<@%s>%s %s' % (self.testbot_userid, colon, msg)
        return msg

    def send_direct_message(self, msg, tobot=True, colon=True):
        msg = self._format_message(msg, tobot, colon)
        self._send_message_to_bot(self.dm_chan, msg)

    def _send_channel_message(self, chan, msg, tobot=True, colon=True):
        msg = self._format_message(msg, tobot, colon)
        self._send_message_to_bot(chan, msg)

    def send_channel_message(self, msg, tobot=True, colon=True):
        self._send_channel_message(self.cm_chan, msg, tobot, colon)

    def send_group_message(self, msg, tobot=True, colon=True):
        self._send_channel_message(self.gm_chan, msg, tobot, colon)

    def wait_for_bot_direct_message(self, match):
        self._wait_for_bot_message(self.dm_chan, match, tosender=False)

    def wait_for_bot_direct_messages(self, matches):
        for match in matches:
            self._wait_for_bot_message(self.dm_chan, match, tosender=False)

    def wait_for_bot_channel_message(self, match, tosender=True):
        self._wait_for_bot_message(self.cm_chan, match, tosender=tosender)

    def wait_for_bot_group_message(self, match):
        self._wait_for_bot_message(self.gm_chan, match, tosender=True)

    def ensure_only_specificmessage_from_bot(self, match, wait=5, tosender=False):
        if tosender is True:
            match = r'^\<@%s\>: %s$' % (self.driver_userid, match)
        else:
            match = r'^%s$' % match

        for _ in xrange(wait):
            time.sleep(1)
            with self._events_lock:
                for event in self.events:
                    if self._is_bot_message(event) and re.match(match, event['text'], re.DOTALL) is None:
                        raise AssertionError(
                            'expected to get message matching "%s", but got message "%s"' % (match, event['text']))

    def ensure_no_channel_reply_from_bot(self, wait=5):
        for _ in xrange(wait):
            time.sleep(1)
            with self._events_lock:
                for event in self.events:
                    if self._is_bot_message(event):
                        raise AssertionError(
                            'expected to get nothing, but got message "%s"' % event['text'])

    def wait_for_file_uploaded(self, name, maxwait=60):
        for _ in xrange(maxwait):
            time.sleep(1)
            if self._has_uploaded_file_rtm(name):
                break
        else:
            raise AssertionError('expected to get file "%s", but got nothing' % name)

    def _send_message_to_bot(self, channel, msg):
        self._start_ts = time.time()
        self.slacker.chat.post_message(channel, msg, username=self.driver_username)

    def _wait_for_bot_message(self, channel, match, maxwait=60, tosender=True):
        for _ in xrange(maxwait):
            time.sleep(1)
            if self._has_got_message_rtm(channel, match, tosender):
                break
        else:
            raise AssertionError('expected to get message like "%s", but got nothing' % match)

    def _has_got_message(self, channel, match, start=None, end=None):
        if channel.startswith('C'):
            match = r'\<@%s\>: %s' % (self.driver_userid, match)
        oldest = start or self._start_ts
        latest = end or time.time()
        func = self.slacker.channels.history if channel.startswith('C') \
               else self.slacker.im.history
        response = func(channel, oldest=oldest, latest=latest)
        for msg in response.body['messages']:
            if msg['type'] == 'message' and re.match(match, msg['text'], re.DOTALL):
                return True
        return False

    def _has_got_message_rtm(self, channel, match, tosender=True):
        if tosender is True:
            match = r'\<@%s\>: %s' % (self.driver_userid, match)
        with self._events_lock:
            for event in self.events:
                if event['type'] == 'message' and re.match(match, event['text'], re.DOTALL):
                    return True
            return False

    def _fetch_users(self):
        response = self.slacker.users.list()
        for user in response.body['members']:
            self.users[user['name']] = user['id']

        self.testbot_userid = self.users[self.testbot_username]
        self.driver_userid = self.users[self.driver_username]

    def _rtm_connect(self):
        r = self.slacker.rtm.start().body
        self.driver_username = r['self']['name']
        self.driver_userid = r['self']['id']

        self.users = {u['name']: u['id'] for u in r['users']}
        self.testbot_userid = self.users[self.testbot_username]

        self._websocket = websocket.create_connection(r['url'])
        self._websocket.sock.setblocking(0)
        thread.start_new_thread(self._rtm_read_forever, tuple())

    def _websocket_safe_read(self):
        """Returns data if available, otherwise ''. Newlines indicate multiple messages """
        data = ''
        while True:
            try:
                data += '{0}\n'.format(self._websocket.recv())
            except:
                return data.rstrip()

    def _rtm_read_forever(self):
        while True:
            json_data = self._websocket_safe_read()
            if json_data != '':
                with self._events_lock:
                    self.events.extend([json.loads(d) for d in json_data.split('\n')])
            time.sleep(1)

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

    def _has_uploaded_file_rtm(self, name):
        with self._events_lock:
            for event in self.events:
                if event['type'] == 'file_shared' \
                   and event['file']['name'] == name \
                   and event['file']['user'] == self.testbot_userid:
                    return True
            return False

    def _join_test_channel(self):
        response = self.slacker.channels.join(self.test_channel)
        self.cm_chan = response.body['channel']['id']
        self._invite_testbot_to_channel()

        groups = self.slacker.groups.list(self.test_group).body['groups']
        for group in groups:
            if self.test_group == group['name']:
                self.gm_chan = group['id']
                self._invite_testbot_to_group(group)
                break
        else:
            raise RuntimeError('Have you created the private group {} for testing?'.format(
                self.group_name))

    def _invite_testbot_to_channel(self):
        if self.testbot_userid not in self.slacker.channels.info(self.cm_chan).body['channel']['members']:
            self.slacker.channels.invite(self.cm_chan, self.testbot_userid)

    def _invite_testbot_to_group(self, group):
        if self.testbot_userid not in group['members']:
            self.slacker.groups.invite(self.gm_chan, self.testbot_userid)

    def _is_bot_message(self, msg):
        if msg['type'] != 'message':
            return False
        if not msg.get('channel', '').startswith('C'):
            return False
        return msg.get('user') == self.testbot_userid \
            or msg.get('username') == self.testbot_username

    def clear_events(self):
        with self._events_lock:
            self.events = []
