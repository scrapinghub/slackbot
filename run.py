import logging
import logging.config
from slackbot import settings
from slackbot.bot import Bot

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)s %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter':'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': True
        },
    }
}

def main():
    logging.config.dictConfig(LOGGING)
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main()
