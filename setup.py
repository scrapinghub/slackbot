from os.path import join, dirname
from setuptools import setup, find_packages

__version__ = open(join(dirname(__file__), 'slackbot/VERSION')).read().strip()

install_requires = (
    'requests>=2.4.0',
    'websocket-client>=0.22.0',
    'importlib>=1.0.3',
    'slacker>=0.5.5',
)

excludes = (
    '*test*',
    '*local_settings*',
)

setup(name='slackbot',
      version=__version__,
      license='BSD',
      description='A simple chat bot for Slack',
      author='Shuai Lin',
      author_email='linshuai2012@gmail.com',
      url='http://github.com/lins05/slackbot',
      platforms=['Any'],
      packages=find_packages(exclude=excludes),
      install_requires=install_requires,
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python'],
      )
