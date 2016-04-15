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
