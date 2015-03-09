import os

KEYS = (
    'testbot_apitoken',
    'testbot_username',
    'driver_apitoken',
    'driver_username',
    'test_channel',
    'test_group',
)

testbot_apitoken = None
testbot_username = None
driver_apitoken = None
driver_username = None
test_channel = None
test_group = None

for key in KEYS:
    envkey = 'SLACKBOT_' + key.upper()
    if envkey in os.environ:
        globals()[key] = os.environ[envkey]

try:
    from .local_settings import *
except ImportError:
    pass

del KEYS
