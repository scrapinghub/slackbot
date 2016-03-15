import pytest

aliases = ['!', '$', 'botbro']
fake_bot_id = 'US99999'
fake_bot_name = '<@' + fake_bot_id + '>'

@pytest.fixture()
def setup_aliases(monkeypatch):
    monkeypatch.setattr('slackbot.settings.ALIASES', ','.join(aliases))


@pytest.fixture()
def dispatcher(monkeypatch):
    from slackbot.dispatcher import MessageDispatcher

    def return_fake_bot_id():
        return fake_bot_id
    dispatcher = MessageDispatcher(None, None)
    monkeypatch.setattr(dispatcher, '_get_bot_id', return_fake_bot_id)
    return dispatcher


def test_aliases(setup_aliases, dispatcher):
    msg = {
        'channel': 'C99999'
    }

    for a in aliases:
        msg['text'] = a + ' hello'
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


def test_botname_works(dispatcher):
    msg = {
        'text': fake_bot_name + ' hello',
        'channel': 'C99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_botname_works_with_aliases_present(setup_aliases, dispatcher):
    msg = {
        'text': fake_bot_name + ' hello',
        'channel': 'G99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'


def test_no_aliases_doesnt_work(dispatcher):
    msg = {
        'channel': 'G99999'
    }
    for a in aliases:
        text = a + ' hello'
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
        'text': fake_bot_name + ' hello',
        'channel': 'D99999'
    }

    msg = dispatcher.filter_text(msg)
    assert msg['text'] == 'hello'
