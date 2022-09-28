import threading
import json
import re
import time
import slacker
import websocket
import six
from six.moves import _thread, range


class Driver(object):
    """Functional tests driver. It handles the communication with slack api, so that
    the tests code can concentrate on higher level logic.
    """
    def __init__(self, driver_apitoken, driver_username, testbot_username, channel, private_channel):
        self.slacker = slacker.Slacker(driver_apitoken)
        self.driver_username = driver_username
        self.driver_userid = None
        self.test_channel = channel
        self.test_private_channel = private_channel
        self.users = {}
        self.testbot_username = testbot_username
        self.testbot_userid = None
        # public channel
        self.cm_chan = None
        # direct message channel
        self.dm_chan = None
        # private private_channel channel
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
        # sleep to allow bot connection to stabilize
        time.sleep(2)

    def wait_for_bot_offline(self):
        self._wait_for_bot_presense(False)

    def _wait_for_bot_presense(self, online):
        for _ in range(10):
            time.sleep(2)
            if online and self._is_testbot_online():
                break
            if not online and not self._is_testbot_online():
                break
        else:
            raise AssertionError('test bot is still {}'.format('offline' if online else 'online'))

    def _format_message(self, msg, tobot=True, toname=False, colon=True,
                        space=True):
        colon = ':' if colon else ''
        space = ' ' if space else ''
        if tobot:
            msg = u'<@{}>{}{}{}'.format(self.testbot_userid, colon, space, msg)
        elif toname:
            msg = u'{}{}{}{}'.format(self.testbot_username, colon, space, msg)
        return msg

    def send_direct_message(self, msg, tobot=False, colon=True):
        msg = self._format_message(msg, tobot, colon)
        self._send_message_to_bot(self.dm_chan, msg)

    def _send_channel_message(self, chan, msg, **kwargs):
        msg = self._format_message(msg, **kwargs)
        self._send_message_to_bot(chan, msg)

    def send_channel_message(self, msg, **kwargs):
        self._send_channel_message(self.cm_chan, msg, **kwargs)

    def send_private_channel_message(self, msg, **kwargs):
        self._send_channel_message(self.gm_chan, msg, **kwargs)

    def wait_for_bot_direct_message(self, match):
        self._wait_for_bot_message(self.dm_chan, match, tosender=False)

    def wait_for_bot_direct_messages(self, matches):
        for match in matches:
            self._wait_for_bot_message(self.dm_chan, match, tosender=False)

    def wait_for_bot_channel_message(self, match, tosender=True):
        self._wait_for_bot_message(self.cm_chan, match, tosender=tosender)

    def wait_for_bot_private_channel_message(self, match, tosender=True):
        self._wait_for_bot_message(self.gm_chan, match, tosender=tosender)

    def wait_for_bot_channel_thread_message(self, match, tosender=False):
        self._wait_for_bot_message(self.gm_chan, match, tosender=tosender, thread=True)

    def wait_for_bot_private_channel_thread_message(self, match, tosender=False):
        self._wait_for_bot_message(self.gm_chan, match, tosender=tosender,
                                   thread=True)

    def ensure_only_specificmessage_from_bot(self, match, wait=5, tosender=False):
        if tosender is True:
            match = six.text_type(r'^\<@{}\>: {}$').format(self.driver_userid, match)
        else:
            match = u'^{}$'.format(match)

        for _ in range(wait):
            time.sleep(1)
            with self._events_lock:
                for event in self.events:
                    if self._is_bot_message(event) and re.match(match, event['text'], re.DOTALL) is None:
                        raise AssertionError(
                            u'expected to get message matching "{}", but got message "{}"'.format(match, event['text']))

    def ensure_no_channel_reply_from_bot(self, wait=5):
        for _ in range(wait):
            time.sleep(1)
            with self._events_lock:
                for event in self.events:
                    if self._is_bot_message(event):
                        raise AssertionError(
                            'expected to get nothing, but got message "{}"'.format(event['text']))

    def wait_for_file_uploaded(self, name, maxwait=30):
        for _ in range(maxwait):
            time.sleep(1)
            if self._has_uploaded_file_rtm(name):
                break
        else:
            raise AssertionError('expected to get file "{}", but got nothing'.format(name))

    def ensure_reaction_posted(self, emojiname, maxwait=5):
        for _ in range(maxwait):
            time.sleep(1)
            if self._has_reacted(emojiname):
                break
        else:
            raise AssertionError('expected to get reaction "{}", but got nothing'.format(emojiname))

    def _send_message_to_bot(self, channel, msg):
        self.clear_events()
        self._start_ts = time.time()
        self.slacker.chat.post_message(channel, msg, username=self.driver_username)

    def _wait_for_bot_message(self, channel, match, maxwait=60, tosender=True, thread=False):
        for _ in range(maxwait):
            time.sleep(1)
            if self._has_got_message_rtm(channel, match, tosender, thread=thread):
                break
        else:
            raise AssertionError('expected to get message like "{}", but got nothing'.format(match))

    def _has_got_message(self, channel, match, start=None, end=None):
        if channel.startswith('C'):
            match = six.text_type(r'\<@{}\>: {}').format(self.driver_userid, match)
        oldest = start or self._start_ts
        latest = end or time.time()
        response = self.slacker.conversations.history(channel=channel, oldest=oldest, latest=latest)
        for msg in response.body['messages']:
            if msg['type'] == 'message' and re.match(match, msg['text'], re.DOTALL):
                return True
        return False

    def _has_got_message_rtm(self, channel, match, tosender=True, thread=False):
        if tosender is True:
            match = six.text_type(r'\<@{}\>: {}').format(self.driver_userid, match)
        with self._events_lock:
            for event in self.events:
                if 'type' not in event or \
                        (event['type'] == 'message' and 'text' not in event):
                    print('Unusual event received: ' + repr(event))
                if (not thread or (thread and event.get('thread_ts', False))) \
                        and event['type'] == 'message' and re.match(match, event['text'], re.DOTALL):
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
        _thread.start_new_thread(self._rtm_read_forever, tuple())

    def _websocket_safe_read(self):
        """Returns data if available, otherwise ''. Newlines indicate multiple messages """
        data = ''
        while True:
            try:
                data += '{0}\n'.format(self._websocket.recv())
            except Exception:
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
        response = self.slacker.conversations.open(users=self.testbot_userid)
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
                if event['type'] == 'message' \
                   and 'files' in event \
                   and event['files'][0]['name'] == name \
                   and event['files'][0]['user'] == self.testbot_userid:
                    return True
            return False

    def _has_reacted(self, emojiname):
        with self._events_lock:
            for event in self.events:
                if event['type'] == 'reaction_added' \
                   and event['user'] == self.testbot_userid \
                   and (event.get('reaction', '') == emojiname \
                        or event.get('name', '') == emojiname):
                    return True
            return False

    def _join_test_channel(self):
        response = self.slacker.channels.join(self.test_channel)
        self.cm_chan = response.body['channel']['id']
        self._invite_testbot_to_channel()

        # Slacker/Slack API's still references to private_channels as 'groups'
        private_channels = self.slacker.groups.list(self.test_private_channel).body['groups']
        for private_channel in private_channels:
            if self.test_private_channel == private_channel['name']:
                self.gm_chan = private_channel['id']
                self._invite_testbot_to_private_channel(private_channel)
                break
        else:
            raise RuntimeError('Have you created the private channel {} for testing?'.format(
                self.test_private_channel))

    def _invite_testbot_to_channel(self):
        if self.testbot_userid not in self.slacker.channels.info(self.cm_chan).body['channel']['members']:
            self.slacker.channels.invite(self.cm_chan, self.testbot_userid)

    def _invite_testbot_to_private_channel(self, private_channel):
        if self.testbot_userid not in private_channel['members']:
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
