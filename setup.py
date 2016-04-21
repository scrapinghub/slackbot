from os.path import join, dirname
from setuptools import setup, find_packages

__version__ = open(join(dirname(__file__), 'asyncbot/VERSION')).read().strip()

install_requires = (
    'requests>=2.4.0',
    'websocket-client>=0.22.0',
    'slacker>=0.5.5',
    'six>=1.10.0'
) # yapf: disable

excludes = (
    '*test*',
    '*local_settings*',
) # yapf: disable

setup(name='asyncbot',
      version=__version__,
      license='BSD',
      description='A simple chat bot for Slack',
      author='Gabriel de Maeztu',
      author_email='gabriel.maeztu@gmail.com',
      url='http://github.com/merqurio/asyncbot',
      platforms=['Any'],
      packages=find_packages(exclude=excludes),
      install_requires=install_requires,
      classifiers=['Development Status :: 3 - Alpha',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5'])
