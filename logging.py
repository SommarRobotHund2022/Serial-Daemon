import time
from sys import argv


DEBUG_MODE = ('--debug' in argv or '-d' in argv) | False
QUIET = ('--quiet' in argv or '-q' in argv)      | False

if (QUIET and DEBUG_MODE):
    print('--debug and --quiet are mutually exclusive')


def timestamp():
    return '[' + time.ctime(time.time()) + ']'

def log(*s, t='I'):
    if not QUIET:
        print(f'{timestamp()} [{t}]', *s)

def log_d(*s, t='I'):
    if DEBUG_MODE and not QUIET:
        print(f'{timestamp()} [DEBUG] [{t}]', *s)
