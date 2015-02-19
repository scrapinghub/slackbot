# coding: UTF-8

from glob import glob
import importlib
import logging
import os
import re
import sys

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.utils import to_utf8, to_unicode, WorkerPool
from slackbot.dispatcher import MessageDispatcher

logger = logging.getLogger(__name__)

class Bot(object):
    def __init__(self):
        self._client = SlackClient(settings.SLACK_TOKEN)
        self._plugins = PluginsManager()
        self._dispatcher = MessageDispatcher(self._client, self._plugins)

    def run(self):
        self._plugins.init()
        self._dispatcher.start()
        self._client.rtm_connect()
        logger.info('connected to slack RTM api')
        self._dispatcher.loop()

class PluginsManager(object):
    commands = {}

    def __init__(self):
        pass

    def init(self):
        plugin_prefix = 'slackbot.plugins'
        plugindir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        for plugin in glob('{}/[!_]*.py'.format(plugindir)):
            module = '.'.join((plugin_prefix, os.path.split(plugin)[-1][:-3]))
            try:
                importlib.import_module(module)
            except:
                logger.exception('Failed to import %s', module)

    def get_plugin(self, text):
        for matcher in self.commands:
            m = matcher.match(text)
            if m:
                return self.commands[matcher], to_utf8(m.groups())
        return None, None

def respond_to(matchstr):
    def wrapper(func):
        PluginsManager.commands[re.compile(matchstr)] = func
        logger.info('registered plugin "%s" to %s', func.__name__, matchstr)
        return func
    return wrapper
