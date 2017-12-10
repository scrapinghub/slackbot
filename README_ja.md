[![PyPI](https://badge.fury.io/py/slackbot.svg)](https://pypi.python.org/pypi/slackbot) [![Build Status](https://secure.travis-ci.org/lins05/slackbot.svg?branch=master)](http://travis-ci.org/lins05/slackbot)

[llimllib/limbo](https://github.com/llimllib/limbo)と[will](https://github.com/skoczen/will)に触発された[Slack](https://slack.com)のチャットボットです。

## 機能

* slack [Real Time Messaging API](https://api.slack.com/rtm) に基づいています
* プラグインの仕組みがシンプルです
* メッセージは同時に処理することができます
* 接続が失われたときに自動的に再接続します
* Python3 をサポートしています
* [Full-fledged functional tests](tests/functional/test_functional.py)

## インストール


```
pip install slackbot
```

## 使用方法

### Slack APIトークンを生成する

まず、ボットのための Slack API トークンを取得する必要があります。それには2つの選択肢があります：

1. もし Slack の [bot user integration](https://api.slack.com/bot-users) を使用している場合は、インテグレーションページで API トークンを取得することができます
2. 実際の Slack ユーザを使用している場合は、[slack web api ページ](https://api.slack.com/web)で API トークンを生成することができます

### ボットを設定する
始めに、あなた自身の slackbot のインスタンスに `slackbot_settings.py` と `run.py` のファイルを作成します。

##### APIトークンを設定する

そして、 `slackbot_settings.py` という Python モジュールで `API_TOKEN` を設定する必要があります。これは Python のインポートパスに置かなければなりません。これはボットによって自動的にインポートされます。

slackbot_settings.py:

```python
API_TOKEN = "<your-api-token>"
```

代わりに、環境変数 `SLACKBOT_API_TOKEN` を使用することもできます。

##### ボットを実行する

```python
from slackbot.bot import Bot
def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
```
##### 既定の回答を設定する
DEFAULT_REPLY を `slackbot_settings.py` に追加します:
```python
DEFAULT_REPLY = "Sorry but I didn't understand you"
```

##### ドキュメントの回答を設定する
[カスタムプラグイン](#create-plugins)に渡される `message` 属性は特別な関数 `message.docs_reply()` を持ち、利用可能なすべてのプラグインを解析し、それぞれのDocを返します。

##### すべてのトレースバックをチャネル、プライベートチャネル、またはユーザーに直接送信する
`slackbot_settings.py` の `ERRORS_TO` に目的の受信者を設定してください。任意のチャネル、プライベートチャネル、またはユーザーが可能です。ボットがあらかじめチャンネルに入っている必要があります。 ユーザーが指定されている場合は、少なくとも1つの DM を最初にボットに送信したことを確認してください。

```python
ERRORS_TO = 'some_channel'
# or...
ERRORS_TO = 'username'
```

##### プラグインの設定をする
[自身のプラグインモジュール](#create-plugins)を`slackbot_settings.py`の`PLUGINS`一覧に追加します:

```python
PLUGINS = [
    'slackbot.plugins',
    'mybot.plugins',
]
```

これであなたの Slack クライアントでボットに話しかけることができます！

### [添付ファイルのサポート](https://api.slack.com/docs/attachments)

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
## プラグインの作成

あなたの利用用途に合わせて拡張/カスタマイズすることができない限り、チャットボットは無意味です。

新しいプラグインを作成するには、単純に `slackbot.bot.respond_to` または `slackbot.bot.listen_to` で装飾された関数を作成します：

- `respond_to` で装飾された関数は、パターンにマッチしたメッセージがボットに送信されたときに呼び出されます（ダイレクトメッセージ、またはチャンネル/プライベートチャンネルチャットの @botname）
- `listen_to` で装飾された関数は、パターンにマッチするメッセージがチャンネル/プライベートチャンネルチャット（ボットに直接送信されない）で送信されたときに呼び出されます。

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

メッセージから params を抽出するには、正規表現を使用します。

```python
from slackbot.bot import respond_to

@respond_to('Give me (.*)')
def giveme(message, something):
    message.reply('Here is {}'.format(something))
```

'stats' や 'stats start_date end_date' のようなコマンドが必要な場合は、次のような正規表現を作成することができます：

```python
from slackbot.bot import respond_to
import re


@respond_to('stat$', re.IGNORECASE)
@respond_to('stat (.*) (.*)', re.IGNORECASE)
def stats(message, start_date=None, end_date=None):
```

プラグインモジュールを slackbot 設定の `PLUGINS` リストに追加します。
例) slackbot_settings.py：

```python
PLUGINS = [
    'slackbot.plugins',
    'mybot.plugins',
]
```

## `@default_reply` デコレータ

*slackbot 0.4.1 で追加されました*

Besides specifying `DEFAULT_REPLY` in `slackbot_settings.py`, you can also decorate a function with the `@default_reply` decorator to make it the default reply handler, which is more handy.

`slackbot_settings.py` に `DEFAULT_REPLY` を指定する以外に、デフォルトの返信ハンドラにするために `@default_reply` デコレータで関数を修飾することもできます。これはもっと便利です。

```python
@default_reply
def my_default_handler(message):
    message.reply('...')
```

デコレータの別の変形例を次に示します。

```python
@default_reply(r'hello.*)')
def my_default_handler(message):
    message.reply('...')
```

上記のデフォルトのハンドラは、（1）指定されたパターンと一致しなければならないメッセージと（2）他の登録されたハンドラによって処理されないメッセージのみを処理します。

## サードパーティプラグインの一覧

[このページ](https://github.com/lins05/slackbot/wiki/Plugins)で利用可能なサードパーティプラグインの一覧を見ることができます.
