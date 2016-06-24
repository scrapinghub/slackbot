# coding: UTF-8
import random
import re

from slackbot.bot import respond_to, listen_to, idle


@respond_to('hello$', re.IGNORECASE)
def hello_reply(message):
    message.reply('hello sender!')


@respond_to('^reply_webapi$')
def hello_webapi(message):
    message.reply_webapi('hello there!', attachments=[{
        'fallback': 'test attachment',
        'fields': [
            {
                'title': 'test table field',
                'value': 'test table value',
                'short': True
            }
        ]
    }])


@respond_to('^reply_webapi_not_as_user$')
def hello_webapi_not_as_user(message):
    message.reply_webapi('hi!', as_user=False)


@respond_to('hello_formatting')
def hello_reply_formatting(message):
    # Format message with italic style
    message.reply('_hello_ sender!')


@listen_to('hello$')
def hello_send(message):
    message.send('hello channel!')


@listen_to('hello_decorators')
@respond_to('hello_decorators')
def hello_decorators(message):
    message.send('hello!')

@listen_to('hey!')
def hey(message):
    message.react('eggplant')


@respond_to(u'你好')
def hello_unicode_message(message):
    message.reply(u'你好!')


# idle tests
IDLE_TEST = {'which': None, 'channel': None}


@respond_to('start idle test ([0-9]+)')
@listen_to('start idle test ([0-9]+)')
def start_idle_test(message, i):
    print("---------- start idle test! -----------")
    IDLE_TEST['which'] = int(i)
    IDLE_TEST['channel'] = message._body['channel']
    print("Idle test is now {which} on channel {channel}".format(**IDLE_TEST))
    # TESTING ONLY, don't rely on this behavior


# idle function testing
# tests 0 and 1: rtm and webapi work from idle function 1
# tests 2 and 3: rtm and webapi work from idle function 2
# test 4: both idle functions can operate simultaneously
@idle
def idle_1(client):
    which = IDLE_TEST['which']
    msg = "I am bored %s" % which
    if which == 0:
        client.rtm_send_message(IDLE_TEST['channel'], msg)
    elif which == 1:
        client.send_message(IDLE_TEST['channel'], msg)
    elif which == 4:
        if random.random() <= 0.5:
            client.rtm_send_message(IDLE_TEST['channel'], "idle_1 is bored")


@idle()
def idle_2(client):
    which = IDLE_TEST['which']
    msg = "I am bored %s" % which
    if which == 2:
        client.rtm_send_message(IDLE_TEST['channel'], msg)
    elif which == 3:
        client.send_message(IDLE_TEST['channel'], msg)
    elif which == 4:
        if random.random() <= 0.5:
            client.rtm_send_message(IDLE_TEST['channel'], "idle_2 is bored")
