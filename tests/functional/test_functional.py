#coding: UTF-8

"""
These functional tests would start a slackbot, and use the slack web api to
drive the tests against the bot.
"""

import os
from os.path import join, abspath, dirname, basename
import subprocess
import pytest
from tests.functional.driver import Driver
from tests.functional.slackbot_settings import (
    testbot_apitoken, testbot_username,
    driver_apitoken, driver_username, test_channel, test_private_channel
)

TRAVIS = 'TRAVIS' in os.environ

def stop_proxy():
    os.system('slackbot-test-ctl stopproxy')

def start_proxy():
    os.system('slackbot-test-ctl startproxy')

def _start_bot_process():
    args = [
        'python',
        'tests/functional/run.py',
    ]
    if TRAVIS:
        args = ['slackbot-test-ctl', 'run'] + args
    env = dict(os.environ)
    env['SLACKBOT_API_TOKEN'] = testbot_apitoken
    env['SLACKBOT_TEST'] = 'true'
    env['PYTHONPATH'] = ':'.join(
        [join(dirname(abspath(__file__))), '../..', env.get('PYTHONPATH', '')])
    return subprocess.Popen(args, env=env)

@pytest.yield_fixture(scope='module') # pylint: disable=E1101
def driver():
    driver = Driver(driver_apitoken,
                    driver_username,
                    testbot_username,
                    test_channel,
                    test_private_channel)
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
    driver.wait_for_bot_direct_message('hello sender!')


def test_bot_respond_to_simple_message_with_webapi(driver):
    driver.send_direct_message('reply_webapi')
    driver.wait_for_bot_direct_message('hello there!')


def test_bot_respond_to_simple_message_with_formatting(driver):
    driver.send_direct_message('hello_formatting')
    driver.wait_for_bot_direct_message('_hello_ sender!')


def test_bot_respond_to_simple_message_case_insensitive(driver):
    driver.send_direct_message('hEllO')
    driver.wait_for_bot_direct_message('hello sender!')


def test_bot_respond_to_simple_message_multiple_plugins(driver):
    driver.send_direct_message('hello_formatting hello')
    driver.wait_for_bot_direct_messages({'hello sender!', '_hello_ sender!'})


def test_bot_direct_message_with_at_prefix(driver):
    driver.send_direct_message('hello', tobot=True)
    driver.wait_for_bot_direct_message('hello sender!')
    driver.send_direct_message('hello', tobot=True, colon=False)
    driver.wait_for_bot_direct_message('hello sender!')


def test_bot_default_reply(driver):
    driver.send_direct_message('youdontunderstandthiscommand do you')
    driver.wait_for_bot_direct_message('.*You can ask me.*')


def test_bot_upload_file(driver):
    driver.send_direct_message('upload slack.png')
    driver.wait_for_bot_direct_message('uploading slack.png')
    driver.wait_for_file_uploaded('slack.png')


def test_bot_upload_file_from_link(driver):
    url = 'https://slack.com/favicon.ico'
    fname = basename(url)
    driver.send_direct_message('upload favicon')
    driver.wait_for_bot_direct_message('uploading <%s>' % url)
    driver.wait_for_file_uploaded(fname)


def test_bot_upload_file_from_content(driver):
    driver.send_direct_message('send_string_content')
    driver.wait_for_file_uploaded('content.txt')


def test_bot_reply_to_channel_message(driver):
    driver.send_channel_message('hello')
    driver.wait_for_bot_channel_message('hello sender!')
    driver.send_channel_message('hello', colon=False)
    driver.wait_for_bot_channel_message('hello sender!')
    driver.send_channel_message('hello', space=False)
    driver.wait_for_bot_channel_message('hello sender!')
    # This is hard for a user to do, but why not test it?
    driver.send_channel_message('hello', colon=False, space=False)
    driver.wait_for_bot_channel_message('hello sender!')


def test_bot_channel_reply_to_name_colon(driver):
    driver.send_channel_message('hello', tobot=False, toname=True)
    driver.wait_for_bot_channel_message('hello sender!')
    driver.send_channel_message('hello', tobot=False, toname=True, space=False)
    driver.wait_for_bot_channel_message('hello sender!')
    driver.send_channel_message('hello', tobot=False, toname=True, colon=False)
    driver.wait_for_bot_channel_message('hello channel!', tosender=False)
    driver.send_channel_message('hello', tobot=False, toname=True, colon=False,
                                space=False)
    driver.wait_for_bot_channel_message('hello channel!', tosender=False)


def test_bot_private_channel_reply_to_name_colon(driver):
    driver.send_private_channel_message('hello', tobot=False, toname=True)
    driver.wait_for_bot_private_channel_message('hello sender!')
    driver.send_private_channel_message('hello', tobot=False, toname=True, space=False)
    driver.wait_for_bot_private_channel_message('hello sender!')
    driver.send_private_channel_message('hello', tobot=False, toname=True, colon=False)
    driver.wait_for_bot_private_channel_message('hello channel!', tosender=False)
    driver.send_private_channel_message('hello', tobot=False, toname=True, colon=False,
                                space=False)
    driver.wait_for_bot_private_channel_message('hello channel!', tosender=False)


def test_bot_listen_to_channel_message(driver):
    driver.send_channel_message('hello', tobot=False)
    driver.wait_for_bot_channel_message('hello channel!', tosender=False)


def test_bot_react_to_channel_message(driver):
    driver.send_channel_message('hey!', tobot=False)
    driver.ensure_reaction_posted('eggplant')


def test_bot_reply_to_private_channel_message(driver):
    driver.send_private_channel_message('hello')
    driver.wait_for_bot_private_channel_message('hello sender!')
    driver.send_private_channel_message('hello', colon=False)
    driver.wait_for_bot_private_channel_message('hello sender!')


def test_bot_ignores_non_related_message_response_tosender(driver):
    driver.send_channel_message('hello', tobot=True)
    driver.ensure_only_specificmessage_from_bot('hello sender!', tosender=True)


def test_bot_ignores_non_related_message_response_tochannel(driver):
    driver.send_channel_message('hello', tobot=False)
    driver.ensure_only_specificmessage_from_bot('hello channel!', tosender=False)


def test_bot_ignores_unknown_message_noresponse_tochannel(driver):
    driver.send_channel_message('unknown message', tobot=False)
    driver.ensure_no_channel_reply_from_bot()


def test_bot_send_usage_unknown_message_response_tosender(driver):
    driver.send_channel_message('unknown message', tobot=True)
    driver.ensure_only_specificmessage_from_bot('Bad command "unknown message".+', tosender=True)


def test_bot_reply_to_message_multiple_decorators(driver):
    driver.send_channel_message('hello_decorators')
    driver.wait_for_bot_channel_message('hello!', tosender=False)
    driver.send_channel_message('hello_decorators', tobot=False)
    driver.wait_for_bot_channel_message('hello!', tosender=False)
    driver.send_direct_message('hello_decorators')
    driver.wait_for_bot_direct_message('hello!')


@pytest.mark.skipif(not TRAVIS, reason="only run reconnect tests on travis builds")
def test_bot_reconnect(driver):
    driver.wait_for_bot_online()
    stop_proxy()
    driver.wait_for_bot_offline()
    start_proxy()
    driver.wait_for_bot_online()
    test_bot_respond_to_simple_message(driver)


def test_bot_reply_with_unicode_message(driver):
    driver.send_direct_message(u'你好')
    driver.wait_for_bot_direct_message(u'你好')
    driver.send_direct_message(u'你不明白，对吗？')
    driver.wait_for_bot_direct_message('.*You can ask me.*')

    driver.send_channel_message(u'你好')
    driver.wait_for_bot_channel_message(u'你好!')
    driver.send_channel_message(u'你不明白，对吗？')
    driver.wait_for_bot_channel_message(u'.*You can ask me.*')


def test_bot_reply_with_alias_message(driver):
    driver.send_channel_message("! hello", tobot=False, colon=False)
    driver.wait_for_bot_channel_message("hello sender!", tosender=True)
    driver.send_channel_message('!hello', tobot=False, colon=False)
    driver.wait_for_bot_channel_message("hello sender!", tosender=True)


def test_bot_reply_thread_in_channel(driver):
    driver.send_channel_message('start a thread', tobot=False, colon=False)
    driver.wait_for_bot_channel_thread_message('I started a thread', tosender=False)


def test_bot_reply_thread_in_private_channel(driver):
    driver.send_private_channel_message('start a thread', tobot=False, colon=False)
    driver.wait_for_bot_private_channel_thread_message('I started a thread', tosender=False)
