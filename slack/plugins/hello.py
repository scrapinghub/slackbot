from slack.bot import respond_to

@respond_to('hello')
def hello():
    yield 'hello!'
