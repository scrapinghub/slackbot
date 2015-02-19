import os

DEBUG = False
SLACK_TOKEN = "<your-token-goes-here>"

try:
    from local_settings import *
except ImportError:
    pass

if 'SLACK_TOKEN' in os.environ:
    SLACK_TOKEN = os.environ['SLACK_TOKEN']
