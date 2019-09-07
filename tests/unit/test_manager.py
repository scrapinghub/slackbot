import re
import sys
import os

import pytest

from slackbot.manager import PluginsManager


@pytest.fixture(scope='session', autouse=True)
def update_path():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_import_plugin_single_module():
    assert 'fake_plugin_module' not in sys.modules
    PluginsManager()._load_plugins('fake_plugin_module')
    assert 'fake_plugin_module' in sys.modules


def test_kwargs():
    pm = PluginsManager()
    pm._load_plugins('kwarg_plugin_module')

    msg = {
        'category': 'respond_to',
        'text': 'Hello, Jeong Arm',
    }

    func, args, kwargs = next(pm.get_plugins(msg['category'], msg['text']))
    assert not args
    assert kwargs == {'name': 'Jeong Arm'}


def test_get_plugins_none_text():
    p = PluginsManager()
    p.commands['respond_to'][re.compile(r'^dummy regexp$')] = lambda x: x
    # Calling get_plugins() with `text == None`
    for func, args, kwargs in p.get_plugins('respond_to', None):
        assert func is None
        assert args is None
        assert kwargs is None
