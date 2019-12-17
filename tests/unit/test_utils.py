from slackbot.utils import get_http_proxy

def test_get_http_proxy():
    environ = {'http_proxy': 'foo:8080'}
    assert get_http_proxy(environ) == ('foo', '8080', None)

    environ = {'http_proxy': 'http://foo:8080'}
    assert get_http_proxy(environ) == ('foo', '8080', None)

    environ = {'no_proxy': '*.slack.com'}
    assert get_http_proxy(environ) == (None, None, '*.slack.com')
