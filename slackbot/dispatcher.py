# -*- coding: utf8 -*-

from glob import glob
import logging
import os
import re
import sys
import time
import traceback

from slackbot.utils import to_utf8, WorkerPool

logger = logging.getLogger(__name__)

AT_MESSAGE_MATCHER = re.compile(r'^\<@(\w+)\>:? (.*)$')

class MessageDispatcher(object):
    def __init__(self, slackclient, plugins):
        self._client = slackclient
        self._pool = WorkerPool(self.dispatch_msg)
        self._plugins = plugins

    def start(self):
        self._pool.start()

    def dispatch_msg(self, msg):
        text = msg['text']
        func, args = self._plugins.get_plugin(text)
        if not func:
            self._default_reply(msg)
        else:
            try:
                func(Message(self._client, msg), *args)
            except:
                logger.exception('failed to handle message %s with plugin "%s"', text, func.__name__)
                reply = '[%s] I have problem when handling "%s"\n' % (func.__name__, text)
                reply += '```\n%s\n```' % traceback.format_exc()
                self._client.rtm_send_message(msg['channel'], reply)
            return

    def _on_new_message(self, msg):
        # ignore edits
        subtype = msg.get('subtype', '')
        if subtype == 'message_changed':
            return

        botname = self._client.login_data['self']['name']
        try:
            msguser = self._client.users.get(msg['user'])
            username = msguser['name']
        except KeyError:
            if 'username' in msg:
                username = msg['username']
            else:
                return

        if username == botname or username == 'slackbot':
            return

        msg = self.filter_text(msg)
        if msg:
            self._pool.add_task(msg)

    def filter_text(self, msg):
        text = msg.get('text', '')
        channel = msg['channel']

        if channel[0] == 'C' or channel[0] == 'G':
            m = AT_MESSAGE_MATCHER.match(text)
            if not m:
                return
            atuser, text = m.groups()
            if atuser != self._client.login_data['self']['id']:
                # a channel message at other user
                return
            logger.debug('got an AT message: %s', text)
            msg['text'] = text
        else:
            m = AT_MESSAGE_MATCHER.match(text)
            if m:
                msg['text'] = m.groups(2)
        return msg

    def loop(self):
        while True:
            events = self._client.rtm_read()
            for event in events:
                if event.get('type') != 'message':
                    continue
                self._on_new_message(event)
            time.sleep(1)

    def _default_reply(self, msg):
        default_reply = [
            u'Bad command "%s", You can ask me one of the following questions:\n' % msg['text'],
        ]
        default_reply += [u'    • `%s`' % str(p.pattern) for p in self._plugins.commands.iterkeys()]

        self._client.rtm_send_message(msg['channel'],
                                     '\n'.join(to_utf8(default_reply)))

class Message(object):
    def __init__(self, slackclient, body):
        self._client = slackclient
        self._body = body

    def _get_user_id(self):
        if 'user' in self._body:
            return self._body['user']

        return self._client.find_user_by_name(self._body['username'])

    def _gen_at_message(self, text):
        text = '<@{}>: {}'.format(self._get_user_id(), text)
        return text

    def reply(self, text):
        chan = self._body['channel']
        if chan.startswith('C') or chan.startswith('G'):
            text = self._gen_at_message(text)
        self._client.rtm_send_message(
            self._body['channel'], to_utf8(text))

    @property
    def channel(self):
        return self._client.get_channel(self._body['channel'])
