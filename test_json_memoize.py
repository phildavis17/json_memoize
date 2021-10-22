# TESTING NOTES

# give it a specific Path

# give it an app name

# give it nothing
# - It should warn you!

import time
import timeit

from json_memoize import memoize


def slow_call(*args, **kwargs):
    time.sleep(5)
    return "slow_call"

#print(timeit.timeit('slow_call()',setup='from __main__ import  slow_call', number=1))

def test_init():
    pass

