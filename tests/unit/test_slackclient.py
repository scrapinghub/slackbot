import pytest

from slackbot.slackclient import SlackClient
from . import slackclient_data


@pytest.fixture
def slack_client():
    c = SlackClient(None, connect=False)
    c.channels = slackclient_data.CHANNELS
    c.users = slackclient_data.USERS
    return c


def test_find_channel_by_name(slack_client):
    assert slack_client.find_channel_by_name('slackbot') == 'D0X6385P1'
    assert slack_client.find_channel_by_name('user') == 'D0X6EF55G'
    assert slack_client.find_channel_by_name('random') == 'C0X4HEKPA'
    assert slack_client.find_channel_by_name('testbot-test') == 'G0X62KL92'


def test_find_user_by_name(slack_client):
    assert slack_client.find_user_by_name('user') == 'U0X4QA7R7'
    assert slack_client.find_user_by_name('slackbot') == 'USLACKBOT'


def test_parse_channel_data(slack_client):
    assert slack_client.find_channel_by_name('fun') is None
    slack_client.parse_channel_data([{
        "id": "C024BE91L",
        "name": "fun",
        "created": 1360782804,
        "creator": "U024BE7LH"
    }])
    assert slack_client.find_channel_by_name('fun') == 'C024BE91L'
    slack_client.parse_channel_data([{
        "id": "C024BE91L",
        "name": "fun2",
        "created": 1360782804,
        "creator": "U024BE7LH"
    }])
    assert slack_client.find_channel_by_name('fun') is None
    assert slack_client.find_channel_by_name('fun2') == 'C024BE91L'

    # Although Slack has changed terminology for 'Groups' (now 'private channels'),
    # The Slack API still uses the `is_group` property for private channels (as of 09/10/2017)
    assert slack_client.find_channel_by_name('test-group-joined') is None
    slack_client.parse_channel_data([{
        'created': 1497473029,
        'creator': "U0X642GBF",
        'id': "G5TV5TW3W",
        'is_archived': False,
        'is_group': True,
        'is_mpim': False,
        'is_open': True,
        'last_read': "0000000000.000000",
        'latest': None,
        'members': ["U0X642GBF"],
        'name': "test-group-joined",
        'name_normalized': "test-group-joined"
    }])
    assert slack_client.find_channel_by_name(
        'test-group-joined') == 'G5TV5TW3W'


def test_parse_user_data(slack_client):
    assert slack_client.find_user_by_name('bob') is None
    slack_client.parse_user_data([{
        'id': 'U123456',
        'name': 'bob'
    }])
    assert slack_client.find_user_by_name('bob') == 'U123456'
    slack_client.parse_user_data([{
        'id': 'U123456',
        'name': 'bob2'
    }])
    assert slack_client.find_user_by_name('bob') is None
    assert slack_client.find_user_by_name('bob2') == 'U123456'


def test_init_with_timeout():
    client = SlackClient(None, connect=False)
    assert client.webapi.api.timeout == 10  # seconds default timeout

    expected_timeout = 42  # seconds
    client = SlackClient(None, connect=False, timeout=expected_timeout)
    assert client.webapi.api.timeout == expected_timeout
