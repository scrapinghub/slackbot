[![PyPI](https://badge.fury.io/py/slackbot.svg)](https://pypi.python.org/pypi/slackbot) [![Build Status](https://secure.travis-ci.org/lins05/slackbot.svg?branch=master)](http://travis-ci.org/lins05/slackbot)

A chat bot for [Slack](https://slack.com) based on [llimllib/slask](https://github.com/llimllib/slask).

## Features

* Based on slack [Real Time Messaging API](https://api.slack.com/rtm)
* Simple plugins mechanism
* Messages can be handled concurrently
* Automatically reconnect to slack when connection is lost

## Installation


```
sudo pip install slackbot
```

## Usage

### Generate the slack api token

First you need to get the slack api token for your bot. You have two options:

1. If you use a [bot user integration](https://api.slack.com/bot-users) of slack, you can get the api token on the integration page.
2. If you use a real slack user, you can generate an api token on [slack web api page](https://api.slack.com/web).

### Configure the api token

Then you need to configure the `API_TOKEN` in a python module `slackbot_settings.py`, which must be located in a python import path.

slackbot_settings.py:

```python
API_TOKEN = "<your-api-token>"
```

Alternatively, you can use the environment variable `SLACK_API_TOKEN`.

### Run the bot

```python
from slackbot.bot import Bot
def main():
    bot = Bot()
    bot.run()
```

Now you can talk to your bot in your slack client!

## Plugins

A chat bot is meaningless unless you can extend/customize it to fit your own use cases.

To write a new plugin, simplely create a function decorated by `slackbot.bot.respond_to` or `slackbot.bot.listen_to`:

- A function decorated with `respond_to` is called when a message matching the pattern is sent to the bot (direct message or @botname in a channel/group chat)
- A function decorated with `listen_to` is called when a message matching the pattern is sent on a channel/group chat (not directly sent to the bot)

```python
from slackbot.bot import respond_to
from slackbot.bot import listen_to

@respond_to('I love you')
def love(message):
    message.reply('I love you too!')

@listen_to('Can someone help me?')
def help(message):
    # Message is replied to the sender (prefixed with @user)
    message.reply('Yes, I can!')

    # Message is sent on the channel
    # message.send('I can help everybody!')
```

To extract params from the message, you can use regular expression:
```python
from slackbot.bot import respond_to

@respond_to('Give me (.*)')
def giveme(message, something):
    message.reply('Here is %s' % something)
```

And add the plugins module to `PLUGINS` list of slackbot settings, e.g. slackbot_settings.py:

```python
PLUGINS = [
    'slackbot.plugins',
    'mybot.plugins',
]
```
