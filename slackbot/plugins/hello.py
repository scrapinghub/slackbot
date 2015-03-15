from slackbot.bot import respond_to
import re

@respond_to('hello', re.IGNORECASE)
def hello(message):
    message.reply('hello!')
