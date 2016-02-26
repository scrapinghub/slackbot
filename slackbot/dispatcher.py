# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import re
import time
import traceback
from six import iteritems
from slackbot.manager import PluginsManager
from slackbot.utils import to_utf8, WorkerPool

logger = logging.getLogger(__name__)

AT_MESSAGE_MATCHER = re.compile(r'^\<@(\w+)\>:? (.*)$')


class Dispatcher(object):
    def __init__(self, slackclient, plugins):
        self._client = slackclient
        self._pool = WorkerPool(self.dispatch)
        self._plugins = plugins

    def start(self):
        self._pool.start()

    def _execute_plugin(self, category, key, params):
        executed = False
        exception = None
        for func, args in self._plugins.get_plugins(category, key):
            if func:
                executed = True
                try:
                    func(params, *args)
                except:
                    logger.exception('Failed to handle message %s with plugin'
                                     ' "%s"', key, func.__name__)
                    exception = ('[%s] I have problem when handling "%s"\n' %
                                 (func.__name__, key))
                    exception += '```\n%s\n```' % traceback.format_exc()
        return executed, exception

    def dispatch(self, event):
        """
        Should dispatch all categories.
        """
        category, payload = event

        logger.debug('dispatching category: %s, payload: %s' %
                     (category, str(payload)))

        if category in ['listen_to', 'respond_to']:
            text = payload['text']
            message = Message(self._client, payload)
            responded, exception = self._execute_plugin(category, text, message)
            if exception is not None:
                self._client.rtm_send_message(payload['channel'], exception)
            if not responded and category == 'responded_to':
                self._default_reply(payload)
        elif category == 'on_reaction':
            reaction = payload['reaction']
            user = payload['user']
            reaction_event = payload['type'] # added/removed
            item = payload['item']
            timestamp = item['ts']
            channel = item['channel']
            item_type = item['type']

            # Note that we can only find messages in public channels.
            message = self._client.get_message(channel=channel, timestamp=timestamp)
            params = { 'user' : user, 'type': reaction_event, 'message' : message }
            executed, exception = self._execute_plugin(category, reaction, params)

            assert executed, "Couldn't find any plugin for %s." % category
            assert exception is None, exception


    def _on_new_message(self, msg):
        # ignore edits
        subtype = msg.get('subtype', '')
        if subtype == 'message_changed':
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

        if username == botname or username == 'slackbot':
            return

        msg_respond_to = self.filter_text(msg)
        if msg_respond_to:
            self._pool.add_task(('respond_to', msg_respond_to))
        else:
            self._pool.add_task(('listen_to', msg))

    def _on_reaction(self, event):
      botname = self._client.login_data['self']['name']
      self._pool.add_task(('on_reaction', event))

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
                if event.get('type') in ['reaction_added', 'reaction_removed']:
                    # only capture reaction events on messages.
                    if event.get('item').get('type') == 'message':
                        self._on_reaction(event)
                    continue
                elif event.get('type') != 'message':
                    continue
                self._on_new_message(event)
            time.sleep(1)

    def _default_reply(self, msg):
        try:
            from slackbot_settings import default_reply
            default_reply = to_utf8(default_reply)

        except ImportError:

            default_reply = [
                'Bad command "%s", You can ask me one of the following questions:\n' % msg['text'],
            ]
            default_reply += ['    • `{0}` {1}'.format(p.pattern, v.__doc__ or "")
                              for p, v in iteritems(self._plugins.commands['respond_to'])]

            default_reply = '\n'.join(to_utf8(default_reply))

        self._client.rtm_send_message(msg['channel'], default_reply)


class Message(object):
    def __init__(self, slackclient, body):
        self._client = slackclient
        self._body = body
        self._plugins = PluginsManager()

    def _get_user_id(self):
        if 'user' in self._body:
            return self._body['user']

        return self._client.find_user_by_name(self._body['username'])

    def _gen_at_message(self, text):
        text = '<@{}>: {}'.format(self._get_user_id(), text)
        return text

    def _gen_reply(self, text):
        chan = self._body['channel']
        if chan.startswith('C') or chan.startswith('G'):
            return self._gen_at_message(text)
        else:
            return text

    def reply_webapi(self, text):
        """
            Send a reply to the sender using Web API

            (This function supports formatted message
            when using a bot integration)
        """
        text = self._gen_reply(text)
        self.send_webapi(text)

    def send_webapi(self, text, attachments=None):
        """
            Send a reply using Web API

            (This function supports formatted message
            when using a bot integration)
        """
        self._client.send_message(
            self._body['channel'],
            to_utf8(text),
            attachments=attachments)
        return Message(self._client, response.body['message'])

    def reply(self, text):
        """
            Send a reply to the sender using RTM API

            (This function doesn't supports formatted message
            when using a bot integration)
        """
        text = self._gen_reply(text)
        self.send(text)

    def send(self, text):
        """
            Send a reply using RTM API

            (This function doesn't supports formatted message
            when using a bot integration)
        """
        return self._client.rtm_send_message(
            self._body['channel'], to_utf8(text))

    def react(self, emojiname):
        """
           React to a message using the web api
        """
        self._client.react_to_message(
            emojiname=emojiname,
            channel=self._body['channel'],
            timestamp=self._body['ts'])

    def reply_channel(self, text):
        text = u'<!channel>: {}'.format(text)
        return self.send_webapi(text)

    @property
    def channel(self):
        return self._client.get_channel(self._body['channel'])

    @property
    def body(self):
        return self._body

    def docs_reply(self):
        reply = ['    • `{0}` {1}'.format(v.__name__, v.__doc__ or "") for p, v in iteritems(self._plugins.commands['respond_to'])]
        return '\n'.join(to_utf8(reply))
