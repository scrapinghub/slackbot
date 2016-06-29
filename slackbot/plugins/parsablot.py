#coding: UTF-8
import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to

import os
from slackbot.bot import respond_to
from slackbot.utils import download_file, create_tmp_file


@respond_to(r'jenkins get \<?(.*)\>?')
def upload(message, build_number):
    url = 'http://10.5.2.100:8080/job/Director - Android/' + build_number + '/artifact/Director/build/outputs/apk/Director-staging-release.apk'
    with create_tmp_file() as tmpf:
        download_file(url, tmpf)
        message.channel.upload_file(fname, tmpf, 'Jenkins Android Build #{}'.format(build_number))


