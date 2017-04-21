import os
from slackbot.bot import respond_to
from slackbot.utils import download_file, create_tmp_file


@respond_to(r'upload \<?(.*)\>?')
def upload(message, url):
    url = url.lstrip('<').rstrip('>')
    message.reply('uploading {}'.format(url))
    if url.startswith('http'):
        with create_tmp_file() as tmpf:
            download_file(url, tmpf)
            message.channel.upload_file(url, tmpf,
                                        'downloaded from {}'.format(url))
    elif url == 'slack.png':
        cwd = os.path.abspath(os.path.dirname(__file__))
        fname = os.path.join(cwd, '../../tests/functional/slack.png')
        message.channel.upload_file(url, fname)
