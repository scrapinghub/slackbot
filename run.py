#!/usr/bin/env python

import sys
import os
import logging
import logging.config


def main():
    if os.environ.get('SLACKBOT_TEST'):
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'tests/functional'))

    from slackbot import settings
    from slackbot.bot import Bot

    kw = {
        'format': '[%(asctime)s] %(message)s',
        'datefmt': '%m/%d/%Y %H:%M:%S',
        'level': logging.DEBUG if settings.DEBUG else logging.INFO,
        'stream': sys.stdout,
    }
    logging.basicConfig(**kw)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main()
