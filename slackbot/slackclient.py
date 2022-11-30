# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import
import os
import json
import logging
import time
from ssl import SSLError
from copy import deepcopy

import slacker
from six import iteritems

from websocket import (
    create_connection, WebSocketException, WebSocketConnectionClosedException
)

from slackbot.utils import to_utf8, get_http_proxy

logger = logging.getLogger(__name__)

def webapi_generic_list(webapi, resource_key, response_key, **kw):
    """Generic <foo>.list request, where <foo> could be users, chanels,
    etc."""
    ret = []
    next_cursor = None
    while True:
        args = deepcopy(kw)
        if resource_key == 'conversations':
            # Slack API says max limit is 1000
            args['limit'] = 800
        if next_cursor:
            args['cursor'] = next_cursor
        response = getattr(webapi, resource_key).list(**args)
        ret.extend(response.body.get(response_key))

        next_cursor = response.body.get('response_metadata', {}).get('next_cursor')
        if not next_cursor:
            break
        logging.info('Getting next page for %s (%s collected)', resource_key, len(ret))
    return ret

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
        self.users = {}
        self.channels = {}
        self.connected = False
        self.rtm_start_args = rtm_start_args

        if timeout is None:
            self.webapi = slacker.Slacker(self.token, rate_limit_retries=30)
        else:
            self.webapi = slacker.Slacker(self.token, rate_limit_retries=30, timeout=timeout)

        if connect:
            self.ensure_connection()

    def rtm_connect(self):
        reply = self.webapi.rtm.start(**(self.rtm_start_args or {})).body
        time.sleep(1)
        self.parse_slack_login_data(reply)

    def ensure_connection(self):
        while True:
            try:
                self.list_users_and_channels()
                self.rtm_connect()
                logger.warning('reconnected to slack rtm websocket')
                return
            except Exception as e:
                logger.exception('failed to reconnect: %s', e)
                time.sleep(5)

    def list_users(self):
        return webapi_generic_list(self.webapi, 'users', 'members')

    def list_channels(self):
        return webapi_generic_list(self.webapi, 'conversations', 'channels', types='public_channel,private_channel,mpim,im')

    def list_users_and_channels(self):
        logger.info('Loading all users')
        self.parse_user_data(self.list_users())
        logger.info('Loaded all users')

        logger.info('Loading all channels')
        self.parse_channel_data(self.list_channels())
        logger.info('Loaded all channels')

    def parse_slack_login_data(self, login_data):
        self.login_data = login_data
        self.domain = self.login_data['team']['domain']
        self.username = self.login_data['self']['name']


        proxy, proxy_port, no_proxy = get_http_proxy(os.environ)

        self.websocket = create_connection(self.login_data['url'], http_proxy_host=proxy,
                                           http_proxy_port=proxy_port, http_no_proxy=no_proxy)

        self.websocket.sock.setblocking(0)

    def parse_channel_data(self, channel_data):
        self.channels.update({c['id']: c for c in channel_data})

    def parse_user_data(self, user_data):
        self.users.update({u['id']: u for u in user_data})

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
                self.ensure_connection()
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
        self.webapi.files.upload(fpath,
                                 channels=channel,
                                 filename=fname,
                                 initial_comment=comment)

    def upload_content(self, channel, fname, content, comment):
        self.webapi.files.upload(None,
                                 channels=channel,
                                 content=content,
                                 filename=fname,
                                 initial_comment=comment)

    def send_message(self, channel, message, attachments=None, as_user=True, thread_ts=None):
        self.webapi.chat.post_message(
                channel,
                message,
                username=self.login_data['self']['name'],
                icon_url=self.bot_icon,
                icon_emoji=self.bot_emoji,
                attachments=attachments,
                as_user=as_user,
                thread_ts=thread_ts)

    def get_channel(self, channel_id):
        return Channel(self, self.channels[channel_id])

    def open_dm_channel(self, user_id):
        return self.webapi.conversations.open(users=user_id).body["channel"]["id"]

    def find_channel_by_name(self, channel_name):
        for channel_id, channel in iteritems(self.channels):
            try:
                name = channel['name']
            except KeyError:
                name = self.users[channel['user']]['name']
            if name == channel_name:
                return channel_id

    def get_user(self, user_id):
        return self.users.get(user_id)

    def find_user_by_name(self, username):
        for userid, user in iteritems(self.users):
            if user['name'] == username:
                return userid

    def react_to_message(self, emojiname, channel, timestamp):
        self.webapi.reactions.add(
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
