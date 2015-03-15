# -*- coding: utf8 -*-

from glob import glob
import imp
import importlib
import logging
import os
import re
import sys
import thread
import time

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.utils import to_utf8, to_unicode, WorkerPool
from slackbot.dispatcher import MessageDispatcher

logger = logging.getLogger(__name__)

class Bot(object):
    def __init__(self):
        self._client = SlackClient(settings.API_TOKEN)
        self._plugins = PluginsManager()
        self._dispatcher = MessageDispatcher(self._client, self._plugins)

    def run(self):
        self._plugins.init_plugins()
        self._dispatcher.start()
        self._client.rtm_connect()
        thread.start_new_thread(self._keepactive, tuple())
        logger.info('connected to slack RTM api')
        self._dispatcher.loop()

    def _keepactive(self):
        logger.info('keep active thread started')
        while True:
            time.sleep(30 * 60)
            self._client.ping()

class PluginsManager(object):
    commands = {}

    def __init__(self):
        pass

    def init_plugins(self):
        if hasattr(settings, 'PLUGINS'):
            plugins = settings.PLUGINS
        else:
            plugins = 'slackbot.plugins'

        for plugin in plugins:
            self._load_plugins(plugin)

    def _load_plugins(self, plugin):
        logger.info('loading plugin "%s"', plugin)
        path_name = None
        for mod in plugin.split('.'):
            if path_name is not None:
                path_name = [path_name]
            _, path_name, _ = imp.find_module(mod, path_name)
        for pyfile in glob('{}/[!_]*.py'.format(path_name)):
            module = '.'.join((plugin, os.path.split(pyfile)[-1][:-3]))
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

def respond_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands[re.compile(matchstr, flags)] = func
        logger.info('registered plugin "%s" to "%s"', func.__name__, matchstr)
        return func
    return wrapper
