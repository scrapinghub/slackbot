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


def test_get_plugins_none_text():
    p = PluginsManager()
    p.commands['respond_to'][re.compile(r'^dummy regexp$')] = lambda x: x
    # Calling get_plugins() with `text == None`
    for func, args in p.get_plugins('respond_to', None):
        assert func is None
        assert args is None


def test_get_plugins_text_starting_with_u00a0():
    p = PluginsManager()
    f = lambda x: x
    p.commands['respond_to'][re.compile(r'^dummy$')] = f
    for func, args in p.get_plugins('respond_to', '\u00a0dummy'):
        assert func == f
        assert len(args) == 0


def test_get_plugins_text_with_u00a0():
    p = PluginsManager()
    f = lambda x: x
    p.commands['respond_to'][re.compile(r'^dummy foo$')] = f
    for func, args in p.get_plugins('respond_to', 'dummy\u00a0foo'):
        assert func == f
        assert len(args) == 0
