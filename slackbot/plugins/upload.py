import os
from slackbot.bot import respond_to
from slackbot.utils import download_file, create_tmp_file


@respond_to(r'upload \<?(.*)\>?')
def upload(message, url):
    url = url.lstrip('<').rstrip('>')
    fname = os.path.basename(url)
    message.reply('uploading {}'.format(fname))
    if url.startswith('http'):
        with create_tmp_file() as tmpf:
            download_file(url, tmpf)
            message.channel.upload_file(fname, tmpf, 'downloaded from {}'.format(url))
    elif url.startswith('/'):
        message.channel.upload_file(fname, url)
