import os

DEBUG = False

PLUGINS = [
    'slackbot.plugins',
]

#API_TOKEN = '###token###'
#BOT_ICON = 'http://lorempixel.com/64/64/abstract/7/'
#BOT_EMOJI = ':godmode:'

for key in os.environ:
    if key[:9] == 'SLACKBOT_':
        name = key[9:]
        globals()[name] = os.environ[key]

try:
    from local_settings import *
except ImportError:
    pass
