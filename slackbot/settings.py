# -*- coding: utf-8 -*-

import os

DEBUG = False

PLUGINS = [
    'slackbot.plugins',
]

ERRORS_TO = None

# API_TOKEN = '###token###'

'''
Setup a comma delimited list of aliases that the bot will respond to.

Example: if you set ALIASES='!,$' then a bot which would respond to:
'botname hello'
will now also respond to
'$ hello'
'''
ALIASES = ''

'''
If you use Slack Web API to send messages (with send_webapi() or reply_webapi()),
you can customize the bot logo by providing Icon or Emoji.
If you use Slack RTM API to send messages (with send() or reply()),
the used icon comes from bot settings and Icon or Emoji has no effect.
'''
# BOT_ICON = 'http://lorempixel.com/64/64/abstract/7/'
# BOT_EMOJI = ':godmode:'

for key in os.environ:
    if key[:9] == 'SLACKBOT_':
        name = key[9:]
        globals()[name] = os.environ[key]

try:
    from slackbot_settings import *
except ImportError:
    try:
        from local_settings import *
    except ImportError:
        pass
