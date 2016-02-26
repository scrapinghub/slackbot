# -*- coding: utf-8 -*-
from __future__ import absolute_import
import imp
import importlib
import logging
import re
import time
from functools import wraps
from glob import glob
from six.moves import _thread
from slackbot import settings
from slackbot.dispatcher import Dispatcher
from slackbot.manager import PluginsManager
from slackbot.slackclient import SlackClient
from slackbot.utils import convert_time

logger = logging.getLogger(__name__)


py_schedule = None
try:
    py_schedule = importlib.import_module('schedules')
except:
    logger.info('disabling schedule plugin')

class Bot(object):
    def __init__(self):
        self._client = SlackClient(
            settings.API_TOKEN,
            bot_icon=settings.BOT_ICON if hasattr(settings, 'BOT_ICON') else None,
            bot_emoji=settings.BOT_EMOJI if hasattr(settings, 'BOT_EMOJI') else None
        )
        self._plugins = PluginsManager()
        self._dispatcher = Dispatcher(self._client, self._plugins)

    def run(self):
        self._plugins.init_plugins()
        self._dispatcher.start()
        self._client.rtm_connect()
        _thread.start_new_thread(self._keepactive, tuple())
        if py_schedule:
            _thread.start_new_thread(self._scheduler, tuple())
        logger.info('connected to slack RTM api')
        self._dispatcher.loop()

    def _keepactive(self):
        logger.info('keep active thread started')
        while True:
            time.sleep(30 * 60)
            self._client.ping()

    def _scheduler(self):
        logger.info('scheduling thread')
        while True:
            # Try finishing up every second.
            time.sleep(1)
            py_schedule.run_pending()

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

def on_reaction(reaction, flags=0):
    def wrapper(func):
        reaction_re = re.compile(re.escape(reaction), flags)
        PluginsManager.commands['on_reaction'][reaction_re] = func
        logger.info('registerd on_reaction plugin "%s" to "%s"', func.__name__, reaction)
        return func
    return wrapper

def schedule(frequency):
    """
    Supports scheduling a task with basic grammer.

    For scheduling a one time task:
        @schedule("in 20 mins")
        def job()
            return

    For scheduling a periodic task:
        @schedule("every 20 minutes")
        def job()
            return

    Similarly:
        @schedule("every 2 hours and 30 minutes")
        @schedule("every Monday at 10:00 AM")
        @schedule("every day at 9:00 AM")

    TODO:
      Support for "on <day> at <time>" format as well.
    """

    assert py_schedule, "@schedule was called without installing 'schedule'"

    def _schedule_decorator(func):
        seconds = re.findall("(\d+)\ssecond", frequency, re.IGNORECASE)
        minutes = re.findall("(\d+)\sminute", frequency, re.IGNORECASE)
        hours = re.findall("(\d+)\shour", frequency, re.IGNORECASE)
        days_of_week = re.findall(
            "monday|tuesday|wednesday|thursday|friday|saturday|sunday",
            frequency,
            re.IGNORECASE)
        every_day = re.findall("\sday\s", frequency, re.IGNORECASE)
        time_tuple = re.findall("at\s(.*)\s(AM|PM)", frequency, re.IGNORECASE)

        # TODO: Sanity checks - only one of minutes, hours, days_of_week should
        # be set at a time.

        time_24hr = '00:00'
        if time_tuple:
            time_24hr = convert_time("%s %s" % (time_tuple[0][0], time_tuple[0][1]))

        time_in_seconds = 0
        if seconds:
            time_in_seconds += int(seconds[0])
        if minutes:
            time_in_seconds += int(minutes[0]) * 60
        if hours:
            time_in_seconds += int(hours[0]) * 60 * 60

        if frequency.startswith('in'):
            # Schedule a one time task.
            @wraps(func)
            def job(*args, **kwargs):
                time.sleep(time_in_seconds)
                return func(*args, **kwargs)

            # Execute this task in a new thread.
            _thread.start_new_thread(job, tuple())
            return
        elif frequency.startswith('every'):
            # Schedule a periodic task.
            if time_in_seconds is not 0 :
                job = py_schedule.every(int(seconds[0])).seconds.do(func)
                logger.debug('scheduled job: %s' % job)
                return

            if every_day:
                job = py_schedule.every().day.at(time_24hr).do(func)
                logger.debug('scheduled job: %s' % job)
                return

            if days_of_week:
                for day_of_week in days_of_week:
                    every = py_schedule.every()
                    day_func = getattr(every, day_of_week.lower())
                    job = day_func.at(time_24hr).do(func)
                    logger.debug('scheduled job: %s' % job)
                return
        elif frequency.startswith('on'):
            # Schedule a one time task at a specific time.
            pass
    return _schedule_decorator
