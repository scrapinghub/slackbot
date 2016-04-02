import os

os.environ['SLACKBOT_TEST'] = 'true'

ALIASES = ",".join(["!", "$"])

def load_driver_settings():
    KEYS = (
        'testbot_apitoken',
        'testbot_username',
        'driver_apitoken',
        'driver_username',
        'test_channel',
        'test_group',
    )

    for key in KEYS:
        envkey = 'SLACKBOT_' + key.upper()
        globals()[key] = os.environ.get(envkey, None)

load_driver_settings()

try:
    from slackbot_test_settings import * # pylint: disable=wrong-import-position
except ImportError:
    pass
