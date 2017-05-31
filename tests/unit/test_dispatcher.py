import pytest

import slackbot.dispatcher


TEST_ALIASES = ['!', '$', 'botbro']
FAKE_BOT_ID = 'US99999'
FAKE_BOT_ATNAME = '<@' + FAKE_BOT_ID + '>'
FAKE_BOT_NAME = 'fakebot'
FAKE_CHANNEL = 'C12942JF92'


class FakePluginManager:
    def raising(self, message):
        raise RuntimeError

    def okay(self, message):
        message.reply('okay')

    def default_okay(self, message):
        message.reply('default_okay')

    def get_plugins(self, category, message):
        if message == 'no_plugin_defined':
            return [[None, None]]
        if category == 'default_reply':
            return [[getattr(self, 'default_'+message), []]]
        else:
            return [[getattr(self, message), []]]


class FakeClient:
    def __init__(self):
        self.rtm_messages = []

    def rtm_send_message(self, channel, message, attachments=None):
        self.rtm_messages.append((channel, message))


class FakeMessage:
    def __init__(self, client, msg):
        self._client = client
        self._msg = msg

    def reply(self, message):
        # Perhaps a bit unnecessary to do it this way, but it's close to how
        # dispatcher and message actually works
        self._client.rtm_send_message(self._msg['channel'], message)


@pytest.fixture()
def setup_aliases(monkeypatch):
    monkeypatch.setattr('slackbot.settings.ALIASES', ','.join(TEST_ALIASES))


@pytest.fixture()
def dispatcher(monkeypatch):
    monkeypatch.setattr('slackbot.settings.DEFAULT_REPLY', 'sorry')
    dispatcher = slackbot.dispatcher.MessageDispatcher(None, None, None)
    monkeypatch.setattr(dispatcher, '_get_bot_id', lambda: FAKE_BOT_ID)
    monkeypatch.setattr(dispatcher, '_get_bot_name', lambda: FAKE_BOT_NAME)
    dispatcher._client = FakeClient()
    dispatcher._plugins = FakePluginManager()
    return dispatcher


def test_aliases(setup_aliases, dispatcher):
    msg = {
        'channel': 'C99999'
    }

    for a in TEST_ALIASES:
        msg['text'] = a + ' hello'
        msg = dispatcher.filter_text(msg)
        assert msg['text'] == 'hello'
        msg['text'] = a + 'hello'
        msg = dispatcher.filter_text(msg)
        assert msg['text'] == 'hello'


def test_nondirectmsg_works(dispatcher):

    # the ID of someone that is not the bot
    other_id = '<@U1111>'
    msg = {
        'text': other_id + ' hello',
        'channel': 'C99999'
    }

    assert dispatcher.filter_text(msg) is None


def test_bot_atname_works(dispatcher):
    msg = {
        'text': FAKE_BOT_ATNAME + ' hello',
        'channel': 'C99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_bot_name_works(dispatcher):
    msg = {
        'channel': 'C99999'
    }

    msg['text'] = FAKE_BOT_NAME + ': hello'
    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'
    msg['text'] = FAKE_BOT_NAME + ':hello'
    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_botname_works_with_aliases_present(setup_aliases, dispatcher):
    msg = {
        'text': FAKE_BOT_ATNAME + ' hello',
        'channel': 'G99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_no_aliases_doesnt_work(dispatcher):
    msg = {
        'channel': 'G99999'
    }
    for a in TEST_ALIASES:
        text = a + ' hello'
        msg['text'] = text
        assert dispatcher.filter_text(msg) is None
        assert msg['text'] == text
        text = a + 'hello'
        msg['text'] = text
        assert dispatcher.filter_text(msg) is None
        assert msg['text'] == text


def test_direct_message(dispatcher):
    msg = {
        'text': 'hello',
        'channel': 'D99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_direct_message_with_name(dispatcher):
    msg = {
        'text': FAKE_BOT_ATNAME + ' hello',
        'channel': 'D99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_dispatch_msg(dispatcher, monkeypatch):
    monkeypatch.setattr('slackbot.dispatcher.Message', FakeMessage)
    dispatcher.dispatch_msg(
        ['reply_to', {'text': 'okay', 'channel': FAKE_CHANNEL}])
    assert dispatcher._client.rtm_messages == [(FAKE_CHANNEL, 'okay')]


def test_dispatch_msg_exception(dispatcher, monkeypatch):
    monkeypatch.setattr('slackbot.dispatcher.Message', FakeMessage)
    dispatcher.dispatch_msg(
        ['reply_to', {'text': 'raising', 'channel': FAKE_CHANNEL}])
    assert len(dispatcher._client.rtm_messages) == 1
    error = dispatcher._client.rtm_messages[0]
    assert error[0] == FAKE_CHANNEL
    assert 'RuntimeError' in error[1]


def test_dispatch_msg_errors_to(dispatcher, monkeypatch):
    monkeypatch.setattr('slackbot.dispatcher.Message', FakeMessage)
    dispatcher._errors_to = 'D12345'
    dispatcher.dispatch_msg(
        ['reply_to', {'text': 'raising', 'channel': FAKE_CHANNEL}])
    assert len(dispatcher._client.rtm_messages) == 2
    user_error = dispatcher._client.rtm_messages[0]
    assert user_error[0] == FAKE_CHANNEL
    error = dispatcher._client.rtm_messages[1]
    assert error[0] == 'D12345'
    assert 'RuntimeError' in error[1]


def test_dispatch_default_msg(dispatcher, monkeypatch):
     monkeypatch.setattr('slackbot.dispatcher.Message', FakeMessage)
     dispatcher.dispatch_msg(
         ['respond_to', {'text': 'no_plugin_defined', 'channel': FAKE_CHANNEL}])
     assert dispatcher._client.rtm_messages == [(FAKE_CHANNEL, 'sorry')]


def test_dispatch_default_msg_plugin(dispatcher, monkeypatch):
    monkeypatch.setattr('slackbot.dispatcher.Message', FakeMessage)
    dispatcher.dispatch_msg(
        ['respond_to', {'text': 'default_okay', 'channel': FAKE_CHANNEL}])
    assert dispatcher._client.rtm_messages == [(FAKE_CHANNEL, 'default_okay')]


def test_none_text(dispatcher):
    # Test for #138: If new msg text is None, fallback to empty str
    msg = {
        'text': None,
        'channel': 'C99999'
    }
    # Should not raise a TypeError
    msg = dispatcher.filter_text(msg)
    assert msg is None
