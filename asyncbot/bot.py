from __future__ import absolute_import
import re
import sys
import time
import logging
from six.moves import _thread
from asyncbot import settings
from asyncbot.manager import PluginsManager
from asyncbot.slackclient import SlackClient
from asyncbot.dispatcher import MessageDispatcher

logger = logging.getLogger(__name__)


class Bot(object):
    def __init__(self, api_token=None, plugins_dir=None, bot_icon=None, bot_emoji=None, default_reply=None):

        if not api_token:
            # Backward compatibility; Looks for a slackbot_settings.py file
            client = SlackClient(
                settings.API_TOKEN,
                bot_icon=settings.BOT_ICON if hasattr(settings, 'BOT_ICON') else None,
                bot_emoji=settings.BOT_EMOJI if hasattr(settings, 'BOT_EMOJI') else None
            )
        else:
            client = SlackClient(api_token, bot_icon=bot_icon, bot_emoji=bot_emoji)

        self._client = client
        self._plugins = PluginsManager(plugins_dir)
        self._dispatcher = MessageDispatcher(self._client, self._plugins, default_reply)

    def run(self):
        self._plugins.init_plugins()
        self._dispatcher.start()
        self._client.rtm_connect()
        _thread.start_new_thread(self._keepactive, tuple())
        logger.info('connected to slack RTM api')
        self._dispatcher.loop()

    def _keepactive(self):
        logger.info('keep active thread started')
        while True:
            time.sleep(30 * 60)
            users = dict((u['id'], u) for u in self._client.webapi.users.list()['body']['members'])
            if users != self._client.users:
                self._client.users = users
            self._client.ping()


def reply_to(matchstr, flags=0):
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
