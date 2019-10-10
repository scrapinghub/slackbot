[![PyPI](https://badge.fury.io/py/slackbot.svg)](https://pypi.python.org/pypi/slackbot) [![Build Status](https://secure.travis-ci.org/lins05/slackbot.svg?branch=master)](http://travis-ci.org/lins05/slackbot)

A chat bot for [Slack](https://slack.com) inspired by [llimllib/limbo](https://github.com/llimllib/limbo) and [will](https://github.com/skoczen/will).

## Features

* Based on slack [Real Time Messaging API](https://api.slack.com/rtm)
* Simple plugins mechanism
* Messages can be handled concurrently
* Automatically reconnect to slack when connection is lost
* Python2 + Python3 Support
* [Full-fledged functional tests](tests/functional/test_functional.py)

## Installation


```
pip install slackbot
```

## Usage

### Generate the slack api token

First you need to get the slack api token for your bot. You have two options:

1. If you use a [bot user integration](https://api.slack.com/bot-users) of slack, you can get the api token on the integration page.
2. If you use a real slack user, you can generate an api token on [slack web api page](https://api.slack.com/web).


### Configure the bot
First create a `slackbot_settings.py` and a `run.py` in your own instance of slackbot.

##### Configure the api token

Then you need to configure the `API_TOKEN` in a python module `slackbot_settings.py`, which must be located in a python import path. This will be automatically imported by the bot.

slackbot_settings.py:

```python
API_TOKEN = "<your-api-token>"
```

Alternatively, you can use the environment variable `SLACKBOT_API_TOKEN`.

##### Run the bot

```python
from slackbot.bot import Bot
def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
```

##### Configure the default answer

Add a DEFAULT_REPLY to `slackbot_settings.py`:
```python
DEFAULT_REPLY = "Sorry but I didn't understand you"
```

##### Configure the docs answer

The `message` attribute passed to [your custom plugins](#create-plugins) has an special function `message.docs_reply()` that will parse all the plugins available and return the Docs in each of them.

##### Send all tracebacks directly to a channel, private channel, or user
Set `ERRORS_TO` in `slackbot_settings.py` to the desired recipient. It can be any channel, private channel, or user. Note that the bot must already be in the channel. If a user is specified, ensure that they have sent at least one DM to the bot first.

```python
ERRORS_TO = 'some_channel'
# or...
ERRORS_TO = 'username'
```

##### Configure the plugins

Add [your plugin modules](#create-plugins) to a `PLUGINS` list in `slackbot_settings.py`:

```python
PLUGINS = [
    'slackbot.plugins',
    'mybot.plugins',
]
```

Now you can talk to your bot in your slack client!

### [Attachment Support](https://api.slack.com/docs/attachments)

```python
from slackbot.bot import respond_to
import re
import json


@respond_to('github', re.IGNORECASE)
def github(message):
    attachments = [
    {
        'fallback': 'Fallback text',
        'author_name': 'Author',
        'author_link': 'http://www.github.com',
        'text': 'Some text',
        'color': '#59afe1'
    }]
    message.send_webapi('', json.dumps(attachments))
```

## Create Plugins

A chat bot is meaningless unless you can extend/customize it to fit your own use cases.

To write a new plugin, simplely create a function decorated by `slackbot.bot.respond_to` or `slackbot.bot.listen_to`:

- A function decorated with `respond_to` is called when a message matching the pattern is sent to the bot (direct message or @botname in a channel/private channel chat)
- A function decorated with `listen_to` is called when a message matching the pattern is sent on a channel/private channel chat (not directly sent to the bot)

```python
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re

@respond_to('hi', re.IGNORECASE)
def hi(message):
    message.reply('I can understand hi or HI!')
    # react with thumb up emoji
    message.react('+1')

@respond_to('I love you')
def love(message):
    message.reply('I love you too!')

@listen_to('Can someone help me?')
def help(message):
    # Message is replied to the sender (prefixed with @user)
    message.reply('Yes, I can!')

    # Message is sent on the channel
    message.send('I can help everybody!')

    # Start a thread on the original message
    message.reply("Here's a threaded reply", in_thread=True)
```

To extract params from the message, you can use regular expression:
```python
from slackbot.bot import respond_to

@respond_to('Give me (.*)')
def giveme(message, something):
    message.reply('Here is {}'.format(something))
```

If you would like to have a command like 'stats' and 'stats start_date end_date', you can create reg ex like so:

```python
from slackbot.bot import respond_to
import re


@respond_to('stat$', re.IGNORECASE)
@respond_to('stat (.*) (.*)', re.IGNORECASE)
def stats(message, start_date=None, end_date=None):
```


And add the plugins module to `PLUGINS` list of slackbot settings, e.g. slackbot_settings.py:

```python
PLUGINS = [
    'slackbot.plugins',
    'mybot.plugins',
]
```

## The `@default_reply` decorator

*Added in slackbot 0.4.1*

Besides specifying `DEFAULT_REPLY` in `slackbot_settings.py`, you can also decorate a function with the `@default_reply` decorator to make it the default reply handler, which is more handy.

```python
@default_reply
def my_default_handler(message):
    message.reply('...')
```

Here is another variant of the decorator:

```python
@default_reply(r'hello.*)')
def my_default_handler(message):
    message.reply('...')
```

The above default handler would only handle the messages which must (1) match the specified pattern and (2) can't be handled by any other registered handler.

## List of third party plugins

You can find a list of the available third party plugins on [this page](https://github.com/lins05/slackbot/wiki/Plugins).
