from slackbot.bot import respond_to

@respond_to('hello')
def hello(message):
    message.reply('hello!')
