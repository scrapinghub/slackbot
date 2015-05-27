import os

DEBUG = False

PLUGINS = [
    'slackbot.plugins',
]

# API_TOKEN = '###token###'

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
