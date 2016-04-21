# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import re
import time
import traceback
import six
from functools import wraps
from asyncbot import settings
from asyncbot.manager import PluginsManager
from asyncbot.utils import WorkerPool

logger = logging.getLogger(__name__)

AT_MESSAGE_MATCHER = re.compile(r'^\<@(\w+)\>:? (.*)$')


class MessageDispatcher(object):
    def __init__(self, slackclient, plugins, default_reply=None):
        self._client = slackclient
        self._pool = WorkerPool(self.dispatch_msg)
        self._plugins = plugins
        self._override_reply = default_reply

    def start(self):
        self._pool.start()

    def dispatch_msg(self, msg):
        category = msg[0]
        msg = msg[1]
        text = msg['text']
        responded = False
        for func, args in self._plugins.get_plugins(category, text):
            if func:
                responded = True
                try:
                    func(Message(self._client, msg), *args)
                except:
                    logger.exception('failed to handle message %s with plugin "%s"', text, func.__name__)
                    reply = u'[{}] I have problem when handling "{}"\n'.format(func.__name__, text)
                    reply += u'```\n{}\n```'.format(traceback.format_exc())
                    self._client.rtm_send_message(msg['channel'], reply)

        if not responded and category == u'respond_to':
            self._default_reply(msg)

    def _on_new_message(self, msg):
        # ignore edits
        subtype = msg.get('subtype', '')
        if subtype == u'message_changed':
            return

        botname = self._client.login_data['self']['name']
        try:
            msguser = self._client.users.get(msg['user'])
            username = msguser['name']
        except (KeyError, TypeError):
            if 'username' in msg:
                username = msg['username']
            else:
                return

        if username == botname or username == u'slackbot':
            return

        msg_respond_to = self.filter_text(msg)
        if msg_respond_to:
            self._pool.add_task(('respond_to', msg_respond_to))
        else:
            self._pool.add_task(('listen_to', msg))

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
                msg['text'] = m.group(2)
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

        def _reply_or_run(message):
            m = Message(self._client, msg)
            if six.callable(message):
                message(m)
            else:
                m.reply(message)

        if self._override_reply:
            _reply_or_run(self._override_reply)

        elif hasattr(settings, 'default_reply'):
            _reply_or_run(settings.default_reply)

        else:
            default_reply = [u'Bad command "{}", You can ask me one of the following questions:\n'.format(msg['text'])]
            default_reply += [u'    • `{0}` {1}'.format(p.pattern, v.__doc__ or "")
                              for p, v in six.iteritems(self._plugins.commands['respond_to'])]
            _reply_or_run(u'\n'.join(default_reply))


def unicode_compact(func):
    """
    Make sure the first parameter of the decorated method to be a unicode
    object.
    """
    @wraps(func)
    def wrapped(self, text, *a, **kw):
        if not isinstance(text, six.text_type):
            text = text.decode('utf-8')
        return func(self, text, *a, **kw)
    return wrapped


class Message(object):
    def __init__(self, slackclient, body):
        self._client = slackclient
        self._body = body
        self._plugins = PluginsManager()

    def _get_user_id(self):
        if 'user' in self._body:
            return self._body['user']

        return self._client.find_user_by_name(self._body['username'])

    @unicode_compact
    def _gen_at_message(self, text):
        text = u'<@{}>: {}'.format(self._get_user_id(), text)
        return text

    @unicode_compact
    def gen_reply(self, text):
        chan = self._body['channel']
        if chan.startswith('C') or chan.startswith('G'):
            return self._gen_at_message(text)
        else:
            return text

    @unicode_compact
    def reply_webapi(self, text):
        """
            Send a reply to the sender using Web API

            (This function supports formatted message
            when using a bot integration)
        """
        text = self.gen_reply(text)
        self.send_webapi(text)

    @unicode_compact
    def send_webapi(self, text, attachments=None):
        """
            Send a reply using Web API

            (This function supports formatted message
            when using a bot integration)
        """
        self._client.send_message(
            self._body['channel'],
            text,
            attachments=attachments)

    @unicode_compact
    def reply(self, text):
        """
            Send a reply to the sender using RTM API

            (This function doesn't supports formatted message
            when using a bot integration)
        """
        text = self.gen_reply(text)
        self.send(text)

    @unicode_compact
    def send(self, text):
        """
            Send a reply using RTM API

            (This function doesn't supports formatted message
            when using a bot integration)
        """
        self._client.rtm_send_message(self._body['channel'], text)

    def react(self, emojiname):
        """
           React to a message using the web api
        """
        self._client.react_to_message(
            emojiname=emojiname,
            channel=self._body['channel'],
            timestamp=self._body['ts'])

    @property
    def channel(self):
        return self._client.get_channel(self._body['channel'])

    @property
    def body(self):
        return self._body

    def docs_reply(self):
        reply = [u'    • `{0}` {1}'.format(v.__name__, v.__doc__ or '')
                 for _, v in six.iteritems(self._plugins.commands['respond_to'])]
        return u'\n'.join(reply)
