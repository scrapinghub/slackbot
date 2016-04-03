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
