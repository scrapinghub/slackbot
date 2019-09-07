from slackbot.bot import respond_to


@respond_to('Hello, (?P<name>.+)')
def say_hello(message, name):
    message.reply('Hello! {}'.format(name))
