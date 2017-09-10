# Slackbot developer guide

Thanks for your interest in developing Slackbot! These notes should help you produce pull requests that will get merged without any issues.

## Style guide

### Code style

There are places in the code that do not follow PEP 8 conventions. Do follow PEP 8 with new code, but do not fix formatting throughout the file you're editing. If your commit has a lot of unrelated reformatting in addition to your new/changed code, you may be asked to resubmit it with the extra changes removed.

### Commits

It's a good idea to use one branch per pull request. This will allow you to work on multiple changes at once.

Most pull requests should contain only a single commit. If you have to make corrections to a pull request, rebase and squash your branch, then do a forced push. Clean up the commit message so it's clear and as concise as needed.

## Developing

These steps will help you prepare your development environment to work on slackbot.

### Clone the repo

Begin by forking the repo. You will then clone your fork and add the central repo as another remote. This will help you incorporate changes as you develop.

```
$ git clone git@github.com:yourusername/slackbot.git
$ cd slackbot
$ git remote add upstream git@github.com:lins05/slackbot.git
```

Do not make commits to develop, even in your local copy. All commits should be on a branch. Start your branch:

```
$ git checkout develop -b name_of_feature
```

To incorporate upstream changes into your local copy and fork:

```
$ git checkout develop
$ git fetch upstream
$ git merge upstream/master
$ git push origin develop
```

See git documentation for info on merging, rebasing, and squashing commits.

### virtualenv/pyvenv

A virtualenv allows you to install the Python packages you need to develop and run slackbot without adding a bunch of unneeded junk to your system's Python installation. Once you create the virtualenv, you need to activate it any time you're developing or running slackbot. The steps are slightly different for Python 2 and Python 3. For Python 2, run:

```
$ virtualenv --no-site-packages .env
```

For Python 3, run:

```
$ pyvenv .env
```

Now that the virtualenv has been created, activate it and install the packages needed for development:

```
$ source .env/bin/activate
$ pip install -r requirements.txt
```

At this point, you should be able to run slackbot as described in the README.

### Configure tests

In order to run tests, you will need a slack instance. Create a free one at http://slack.com. Do not use an existing Slack for tests. The tests produce quite a bit of chat, and depending on how you set up Travis, it's possible for your API tokens to get leaked. Don't risk it. Use a slack created just for development and test.

Create a file named `slackbot_test_settings.py` and add the following settings:

```
testbot_apitoken = 'xoxb-token'
testbot_username = 'testbot'
driver_apitoken = 'xoxp-token'
driver_username = 'your username'
test_channel = 'testchannel'
test_private_channel = 'testprivatechannel'
```

**Important note:** The bot token can be obtained by adding a custom bot integration in Slack. User tokens can be obtained at https://api.slack.com/docs/oauth-test-tokens. Slack tokens are like passwords! Don't commit them. If you're using them in some kind of Github or Travis automation, ensure they are for Slacks that are only for testing.

At this point, you should be able to run tests:

```
$ py.test
```

If you're signed into slack, you'll see your user account and bot account chatting with each other as the tests run.

Tox is also available. If your system has Python 2.7, 3.4, and 3.5 installed, installing and running tox will automatically manage the virtual Python environments and dependencies for you.

### Configure Travis

Log in to Travis and enable tests for your slackbot fork. Open Travis settings. You must add the following environment variables, which should correlate to settings in `slackbot_test_settings.py`:

- SLACKBOT_TESTBOT_APITOKEN
- SLACKBOT_TESTBOT_USERNAME
- SLACKBOT_DRIVER_APITOKEN
- SLACKBOT_DRIVER_USERNAME
- SLACKBOT_TEST_CHANNEL
- SLACKBOT_TEST_PRIVATE_CHANNEL

You must also set `Limit concurrent jobs` to `1`. If you don't, you will see false positives/failures, especially in the test cases that verify slackbot's ability to automatically reconnect on disconnection.
