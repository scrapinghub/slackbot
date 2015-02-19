#!/usr/bin/env python
# coding: UTF-8

from glob import glob
import importlib
import logging
import os
import re
import sys
import time
import traceback
import thread
import Queue

from slack import settings
from slack.slackclient import SlackClient
from slack.utils import to_utf8, to_unicode

logger = logging.getLogger(__name__)

def respond_to(matchstr):
    def wrapper(func):
        Bot.commands[re.compile(matchstr)] = func
        logger.info('registered plugin "%s" to %s', func.__name__, matchstr)
        return func
    return wrapper

class Bot(object):
    dm_matcher = re.compile(r'^\<@(\w+)\>: (.*)$')
    commands = {}

    def __init__(self):
        self.client = SlackClient(settings.SLACK_TOKEN)
        self.pool = WorkerPool(self.dispatch_msg)

    def run(self):
        self.init_plugins()
        self.pool.start()
        if self.client.rtm_connect():
            logger.info('connected to slack RTM api')
            while True:
                events = self.client.rtm_read()
                for event in events:
                    if event.get('type') != 'message':
                        continue
                    self.handle_message(event)
                time.sleep(1)
        else:
            logger.warn("Connection Failed, invalid token <{0}>?".format(settings.SLACK_TOKEN))

    def init_plugins(self):
        plugin_prefix = 'slack.plugins'
        plugindir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")
        # Import the plugins submodule (however named) and set the
        # bot object in it to self
        importlib.import_module(plugin_prefix)
        sys.modules[plugin_prefix].bot = self

        for plugin in glob('{}/[!_]*.py'.format(plugindir)):
            module = '.'.join((plugin_prefix, os.path.split(plugin)[-1][:-3]))
            try:
                importlib.import_module(module)
            except:
                logger.exception('Failed to import %s', module)

    def handle_message(self, msg):
        # ignore bot messages and edits
        subtype = msg.get("subtype", "")
        # if subtype == "bot_message" or subtype == "message_changed":
        #     return
        if subtype == "message_changed":
            return

        botname = self.client.server.login_data["self"]["name"]
        try:
            msguser = self.client.server.users.get(msg["user"])
            username = msguser['name']
        except KeyError:
            logger.debug("msg {0} has no user".format(msg))
            if 'username' in msg:
                username = msg['username']
            else:
                return

        if username == botname or username == "slackbot":
            return

        msg = self.filter_text(msg)
        if msg:
            self.pool.add_task(msg)

    def filter_text(self, msg):
        text = msg.get('text', '')
        channel = msg['channel']

        if channel[0] == 'C':
            m = self.dm_matcher.match(text)
            if not m:
                return
            atuser, text = m.groups()
            if atuser != self.client.server.login_data['self']['id']:
                # a channel message at other user
                return
            logger.debug('got an AT message: %s', text)
            msg['text'] = text
        else:
            m = self.dm_matcher.match(text)
            if m:
                msg['text'] = m.groups(2)
        return msg

    def dispatch_msg(self, msg):
        text = msg['text']
        for matcher in self.commands:
            m = matcher.match(text)
            if m:
                try:
                    args = to_utf8(m.groups())
                    for reply in self.commands[matcher](*args):
                        self.handle_reply(msg['channel'], reply)
                    return
                except:
                    logger.exception('failed to handle message %s', text)
                    reply = 'I have problem when handling "%s"\n' % text
                    reply += '```\n%s\n```' % traceback.format_exc()
                    self.client.rtm_send_message(msg["channel"], reply)
                return

        default_reply = [
            u'Bad command "%s", You can ask me one of the following questsion:\n' % text,
        ]
        default_reply += [u'    • %s' % str(f.__name__) for f in self.commands.itervalues()]

        self.client.rtm_send_message(msg["channel"],
                                     '\n'.join(to_utf8(default_reply)))

    def handle_reply(self, channel, reply):
        if isinstance(reply, basestring):
            self.client.rtm_send_message(channel, to_utf8(reply))
        elif isinstance(reply, tuple):
            self.client.upload_file(channel, to_utf8(reply[1]), to_utf8(reply[2]), to_utf8(reply[3]))

class WorkerPool(object):
    def __init__(self, func, nworker=10):
        self.nworker = nworker
        self.func = func
        self.queue = Queue.Queue()

    def start(self):
        for _ in xrange(self.nworker):
            thread.start_new_thread(self.do_work, tuple())

    def add_task(self, msg):
        self.queue.put(msg)

    def do_work(self):
        while True:
            msg = self.queue.get()
            self.func(msg)

if __name__ == '__main__':
    bot = Bot()
    bot.run()
