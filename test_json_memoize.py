# TESTING NOTES

# give it a specific Path

# give it an app name

# give it nothing
# - It should warn you!

import time
import timeit

from json_memoize import JsonCache, memoize
from pathlib import Path

def fast_call(*args, **kwargs):
    return "fast_call"

def slow_call(*args, **kwargs):
    time.sleep(5)
    return "slow_call"

#print(timeit.timeit('slow_call()',setup='from __main__ import  slow_call', number=1))

def test_init():
    assert JsonCache() is not None

def test_init_with_args():
    test_objet = JsonCache(
        cache_file_path= Path("./"),
        max_size=10,
        max_age=600,
        force_update=True,
        
        )