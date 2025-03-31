def hello():
    print('world')


class Foo:
    """Bar"""


def baz():
    print('this is not tested')


def branch(cond1, cond2):
    if cond1:
        print('condition tested both ways')
    if cond2:
        print('condition not tested both ways')
