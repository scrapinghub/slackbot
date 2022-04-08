# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import
import os
import json
import logging
import time
from ssl import SSLError

from slack_sdk import WebClient
from six import iteritems

from websocket import (
    create_connection, WebSocketException, WebSocketConnectionClosedException
)

from slackbot.utils import to_utf8, get_http_proxy

logger = logging.getLogger(__name__)


class SlackClient(object):
    def __init__(self, token, timeout=None, bot_icon=None, bot_emoji=None, connect=True,
                 rtm_start_args=None):
        self.token = token
        self.bot_icon = bot_icon
        self.bot_emoji = bot_emoji
        self.username = None
        self.domain = None
        self.login_data = None
        self.websocket = None
        self.connected = False
        self.rtm_start_args = rtm_start_args

        if timeout is None:
            self.webapi = WebClient(self.token)
        else:
            self.webapi = WebClient(self.token, timeout=timeout)

        if connect:
            self.rtm_connect()

    def rtm_connect(self):
        reply = self.webapi.rtm_connect(**(self.rtm_start_args or {})).validate()
        time.sleep(1)
        self.parse_slack_login_data(reply)

    def reconnect(self):
        while True:
            try:
                self.rtm_connect()
                logger.warning('reconnected to slack rtm websocket')
                return
            except Exception as e:
                logger.exception('failed to reconnect: %s', e)
                time.sleep(5)

    def parse_slack_login_data(self, login_data):
        self.login_data = login_data
        self.domain = self.login_data['team']['domain']
        self.username = self.login_data['self']['name']

        proxy, proxy_port, no_proxy = get_http_proxy(os.environ)

        self.websocket = create_connection(self.login_data['url'], http_proxy_host=proxy,
                                           http_proxy_port=proxy_port, http_no_proxy=no_proxy)

        self.websocket.sock.setblocking(0)

    def send_to_websocket(self, data):
        """Send (data) directly to the websocket."""
        data = json.dumps(data)
        self.websocket.send(data)

    def ping(self):
        return self.send_to_websocket({'type': 'ping'})

    def websocket_safe_read(self):
        """Returns data if available, otherwise ''. Newlines indicate multiple messages """
        data = ''
        while True:
            try:
                data += '{0}\n'.format(self.websocket.recv())
            except WebSocketException as e:
                if isinstance(e, WebSocketConnectionClosedException):
                    logger.warning('lost websocket connection, try to reconnect now')
                else:
                    logger.warning('websocket exception: %s', e)
                self.reconnect()
            except Exception as e:
                if isinstance(e, SSLError) and e.errno == 2:
                    pass
                else:
                    logger.warning('Exception in websocket_safe_read: %s', e)
                return data.rstrip()

    def rtm_read(self):
        json_data = self.websocket_safe_read()
        data = []
        if json_data != '':
            for d in json_data.split('\n'):
                data.append(json.loads(d))
        return data

    def rtm_send_message(self, channel, message, attachments=None, thread_ts=None):
        message_json = {
            'type': 'message',
            'channel': channel,
            'text': message,
            'attachments': attachments,
            'thread_ts': thread_ts,
            }
        self.send_to_websocket(message_json)

    def upload_file(self, channel, fname, fpath, comment):
        fname = fname or to_utf8(os.path.basename(fpath))
        with open(fname, 'rb') as handle:
            self.webapi.files_upload(handle,
                                     channels=channel,
                                     filename=fname,
                                     initial_comment=comment)

    def upload_content(self, channel, fname, content, comment):
        self.webapi.files_upload(None,
                                 channels=channel,
                                 content=content,
                                 filename=fname,
                                 initial_comment=comment)

    def send_message(self, channel, message, attachments=None, as_user=True, thread_ts=None):
        self.webapi.chat_postMessage(
                channel,
                message,
                username=self.login_data['self']['name'],
                icon_url=self.bot_icon,
                icon_emoji=self.bot_emoji,
                attachments=attachments,
                as_user=as_user,
                thread_ts=thread_ts)

    def get_channel(self, channel_id):
        reply = self.webapi.channels_info(channel_id)
        if reply['ok']:
            return Channel(self, reply['channel'])

    def open_dm_channel(self, user_id):
        return self.webapi.im_open(user_id)["channel"]["id"]

    def find_channel_by_name(self, channel_name):
        reply = self.webapi.channels_list()
        if reply['ok']:
            for ch in reply['channels']:
                if ch['name'] == channel_name:
                    return ch['id']

        # Could be a IM channel
        user = self.find_user_by_name(channel_name)
        if user:
            return user['id']

    def find_user_by_name(self, username):
        reply = self.webapi.users_list()

        if reply['ok']:
            for user in reply['members']:
                if user['name'] == username:
                    return user['id']

    def get_user(self, user_id):
        reply = self.webapi.users_info(user=user_id)

        if reply['ok']:
            return reply['user']

    def react_to_message(self, emojiname, channel, timestamp):
        self.webapi.reactions_add(
            name=emojiname,
            channel=channel,
            timestamp=timestamp)


class SlackConnectionError(Exception):
    pass


class Channel(object):
    def __init__(self, slackclient, body):
        self._body = body
        self._client = slackclient

    def __eq__(self, compare_str):
        name = self._body['name']
        cid = self._body['id']
        return name == compare_str or "#" + name == compare_str or cid == compare_str

    def upload_file(self, fname, fpath, initial_comment=''):
        self._client.upload_file(
            self._body['id'],
            to_utf8(fname),
            to_utf8(fpath),
            to_utf8(initial_comment)
        )

    def upload_content(self, fname, content, initial_comment=''):
        self._client.upload_content(
            self._body['id'],
            to_utf8(fname),
            to_utf8(content),
            to_utf8(initial_comment)
        )
