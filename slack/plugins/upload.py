import os
from slack.bot import respond_to
from slack.utils import download_file, create_tmp_file

@respond_to(r'upload \<?(.*)\>?')
def upload(url):
    url = url.lstrip('<').rstrip('>')
    fname = os.path.basename(url)
    yield 'uploading %s' % fname
    if url.startswith('http'):
        with create_tmp_file() as tmpf:
            download_file(url, tmpf)
            yield 'file', fname, tmpf, 'downloaded from %s' % url
    elif url.startswith('/'):
        yield 'file', fname, url, ''
