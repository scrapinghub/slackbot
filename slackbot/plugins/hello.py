#coding: UTF-8
import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to


@respond_to('hello$', re.IGNORECASE)
def hello_reply(message):
    message.reply('hello sender!')


@respond_to('hello_formatting')
def hello_reply_formatting(message):
    # Format message with italic style
    message.reply('_hello_ sender!')


@listen_to('hello$')
def hello_send(message):
    message.send('hello channel!')


@listen_to('hello_decorators')
@respond_to('hello_decorators')
def hello_decorators(message):
    message.send('hello!')

@listen_to('hey!')
def hey(message):
    message.react('eggplant')


@respond_to(u'你好')
def hello_unicode_message(message):
    message.reply(u'你好!')
