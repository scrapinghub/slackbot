#!/usr/bin/env python

"""This function tests would start a slackbot, and use slack web api to drive
the tests agains the bot.
"""

import os
import subprocess
import pytest
from os.path import join, abspath, dirname, basename
from tests.functional.driver import Driver
from tests.functional.settings import (
    testbot_apitoken, testbot_username,
    driver_apitoken, driver_username, test_channel
)


def _start_bot_process():
    args = [
        'python',
        'run.py',
    ]
    env = dict(os.environ)
    env['SLACK_TOKEN'] = testbot_apitoken
    return subprocess.Popen(args, env=env)

@pytest.yield_fixture(scope='module') # pylint: disable=E1101
def driver():
    driver = Driver(driver_apitoken, driver_username, testbot_username, test_channel)
    driver.start()
    p = _start_bot_process()
    driver.wait_for_bot_online()
    yield driver
    p.terminate()

@pytest.fixture(autouse=True)   # pylint: disable=E1101
def clear_events(driver):
    driver.clear_events()

def test_bot_get_online(driver): # pylint: disable=W0613
    pass

def test_bot_respond_to_simple_message(driver):
    driver.send_direct_message('hello')
    driver.wait_for_bot_direct_message('hello!')

def test_bot_default_reply(driver):
    driver.send_direct_message('youdonunderstandthiscommand donnot you')
    driver.wait_for_bot_direct_message('.*You can ask me.*')

def test_bot_upload_file(driver):
    png = join(abspath(dirname(__file__)), 'slack.png')
    driver.send_direct_message('upload %s' % png)
    driver.wait_for_bot_direct_message('uploading slack.png')
    driver.wait_for_file_uploaded('slack.png')

def test_bot_upload_file_from_link(driver):
    url = 'https://slack.com/favicon.ico'
    fname = basename(url)
    driver.send_direct_message('upload %s' % url)
    driver.wait_for_bot_direct_message('uploading %s' % fname)

def test_bot_reply_to_channel_message(driver):
    driver.send_channel_message('hello')
    driver.wait_for_bot_channel_message('hello!')

def test_bot_ignores_non_related_channel_message(driver):
    driver.send_channel_message('hello', tobot=False)
    driver.ensure_no_channel_reply_from_bot()
