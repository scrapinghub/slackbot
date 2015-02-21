import os

DEBUG = False

PLUGINS = [
    'slackbot.plugins',
]

for key in os.environ:
    if key[:9] == 'SLACKBOT_':
        name = key[9:]
        globals()[name] = os.environ[key]

try:
    from local_settings import *
except ImportError:
    pass
