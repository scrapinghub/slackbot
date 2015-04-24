# -*- coding: utf8 -*-

from glob import glob
import imp
import importlib
import logging
import os
import re
import thread
import time

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.utils import to_utf8
from slackbot.dispatcher import MessageDispatcher

logger = logging.getLogger(__name__)


class Bot(object):
    def __init__(self):
        self._client = SlackClient(
            settings.API_TOKEN,
            bot_icon = settings.BOT_ICON if hasattr(settings, 'BOT_ICON') else None,
            bot_emoji = settings.BOT_EMOJI if hasattr(settings, 'BOT_EMOJI') else None
        )
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
    commands = {
        'respond_to': {},
        'listen_to': {}
    }

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

    def get_plugins(self, category, text):
        has_matching_plugin = False
        for matcher in self.commands[category]:
            m = matcher.search(text)
            if m:
                has_matching_plugin = True
                yield self.commands[category][matcher], to_utf8(m.groups())

        if not has_matching_plugin:
            yield None, None


def respond_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['respond_to'][re.compile(matchstr, flags)] = func
        logger.info('registered respond_to plugin "%s" to "%s"', func.__name__, matchstr)
        return func
    return wrapper


def listen_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['listen_to'][re.compile(matchstr, flags)] = func
        logger.info('registered listen_to plugin "%s" to "%s"', func.__name__, matchstr)
        return func
    return wrapper
