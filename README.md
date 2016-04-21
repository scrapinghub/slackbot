[![PyPI](https://badge.fury.io/py/slackbot.svg)](https://pypi.python.org/pypi/slackbot) [![Build Status](https://secure.travis-ci.org/lins05/slackbot.svg?branch=master)](http://travis-ci.org/lins05/slackbot)

A chat bot for [Slack](https://slack.com) inspired by [llimllib/limbo](https://github.com/llimllib/limbo) and [will](https://github.com/skoczen/will).
A fork from [lins05/slackbot](https://github.com/lins05/slackbot)

## Features

* Based on slack [Real Time Messaging API](https://api.slack.com/rtm)
* Simple plugins mechanism
* Messages can be handled concurrently
* Automatically reconnect to slack when connection is lost
* Python3 Support
* [Full-fledged functional tests](tests/functional/test_functional.py)

## Index:
1. [Installation](#installation)
1. [Usage](#usage)
1. [Create custom plugins](#create-plugins)
1. [Discussion](#discussion)

## Installation


```
sudo pip install slackbot
```

## Usage

### Generate the slack api token

First you need to get the slack api token for your bot. You have two options:

1. If you use a [bot user integration](https://api.slack.com/bot-users) of slack, you can get the api token on the integration page.
2. If you use a real slack user, you can generate an api token on [slack web api page](https://api.slack.com/web).


### Configure the bot
Make sure you have [installed](#installation) slackbot and then create a `run.py` with your own instance of slackbot. like this:

```python
from slackbot.bot import Bot

def main():
    bot = Bot(
        api_token="YOUR_SLACK_API_TOKEN",
        plugins=["path_to_plugins"],
        default_reply="Hello World"
    )
    bot.run()

if __name__ == "__main__":
    main()
```

##### Run the bot
Launch the file from your shell. We recommend to daemonize the process.
```shell
python run.py
```

##### Default reply
The default reply can be either a string or a function. This will be executed whenever the bot doesn't recognize a pattern.

If you decide to create your own function, you will have to create a Message instance. This way you can access any variable at the client you might be interested on.
```python
def my_func(message):
    message.reply("Whatever")
```

###### Configure the docs answer
The `Message` object, the same one is passed instantiated as an attribute to [your custom plugins](#create-plugins) has an special function `message.docs_reply()` that will parse all the plugins available and return the `__doc__` in each one of them as a message.

##### Configure the plugins
Add [your plugin modules](#create-plugins) to the instantiation of your bot:

```python
Bot(
    "API_TOKEN",
    plugins = [
        'slackbot.plugins',
        'mybot.plugins'
    ]
)
```

Now you can talk to your bot in your slack client!

### [Attachment Support](https://api.slack.com/docs/attachments)

```python
from slackbot.bot import respond_to
import re
import json


@respond_to('github', re.IGNORECASE)
def github():
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

- A function decorated with `respond_to` is called when a message matching the pattern is sent to the bot (direct message or @botname in a channel/group chat)
- A function decorated with `listen_to` is called when a message matching the pattern is sent on a channel/group chat (not directly sent to the bot)

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
    # message.send('I can help everybody!')
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


Add the string representing the python module you created:

```python
my_bot = Bot(
    "API_TOKEN",
    plugins = [
        'mybot.plugins'
    ]
)
```

## Discussion

* :hash: #python-slackbot on [freenode](https://webchat.freenode.net/?channels=python-slackbot)
