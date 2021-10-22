import inspect
import json
import logging

from appdirs import AppDirs

from datetime import datetime, timezone
from functools import partial, wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union

default_dirs = AppDirs()

DEFAULT_PATH = Path(default_dirs.user_cache_dir)


"""
def memoize(func = None, cache_dir: Path = None, app_name: str = None, max_size: int = 0, max_age: int = 0, force_update:bool = False) -> Callable:
    # PATH SETUP LOGIC
    #
    # If there's a specific path, use that
    # Else, if there's an appname, use that to make a path
    # Else use the default path (json_memoize) and log a warning
    #   - use 'json_memoize' as the folder name
    
    cache_dir = construct_cache_folder_path(cache_folder=cache_dir, app_name=app_name)
    if app_name is None:
        cur_frame = inspect.currentframe()
        if cur_frame and inspect.isframe(cur_frame):
            cur_file = inspect.getframeinfo(cur_frame.f_back).filename
            cache_dir = Path(cache_dir) / Path(cur_file).stem
        else:
            cache_dir = Path(cache_dir) / "default"


    if cache_dir is None:
            frame = inspect.getframeinfo(inspect.currentframe().f_back)
            cache_dir = Path(default_dirs.user_cache_dir) / Path(frame.filename).stem
    if func is None:
        return partial(memoize, cache_dir=cache_dir, max_size=max_size, max_age=max_age, force_update=force_update)
    @wraps(func)
    def cache_wrapper(*args, **kwargs):
        cache_file_path = Path(cache_dir) / f"{func.__name__}_cache"
        # Log a warning if a supplied argument does not have a good string representation
        for arg in args:
            _warn_if_repr(arg)
        for k, v in kwargs:
            _warn_if_repr(k)
            _warn_if_repr(v)
        call_string = f"{args}, {kwargs}"
        with JsonCache(cache_file_path, max_size=max_size, max_age=max_age, force_update=force_update) as cache:
            if call_string not in cache:
                cache.store(call_string, func(*args, **kwargs))
                logging.info("%s cached.", call_string)
            return cache.retrieve(call_string)
    return cache_wrapper
"""

def memoize(
        func: Callable = None,
        cache_folder_path: Path = None,
        app_name: str = None,
        cache_file_name: str = None,
        max_age: int = 0,
        max_size: int = 0,
        force_update: bool = False
    ):
        if func is None:
            return partial(memoize, cache_folder_path=cache_folder_path, app_name=app_name, cache_file_name=cache_file_name, max_age=max_age, max_size=max_size, force_update=force_update)
        @wraps(func)
        def cache_wrapper(*args, **kwargs):
            cache_folder = construct_cache_folder_path(cache_folder_path, app_name)
            cache_file_path = Path(cache_folder) / cache_file_name or f"{func.__name__}"
            for arg in [*args, *kwargs.keys(), *kwargs.values()]:
                _warn_if_repr(arg)
            



def _warn_if_repr(item: Any) -> None:
    """Logs a warning if a call to the supplied item's __str__ returns something that looks like a __repr__ output."""
    str_rep = str(item)
    if "<" in str_rep and ">" in str_rep:
        logging.warn("%s <-- This looks like it might be a repr output. Cache may not behave as expected.", str_rep)


def construct_cache_folder_path(cache_folder_path: Optional[Path], app_name: Optional[str]) -> Path:
    if cache_folder_path is not None:
        return Path(cache_folder_path)
    elif app_name is not None and app_name:
        return Path(AppDirs(appname=app_name).user_cache_dir)
    else:
        logging.warn("Caching in default folder is not recommended. Provide app_name or cache_folder.")
        return Path(AppDirs().user_cache_dir) / "json_memoize"


def make_timestamp() -> float:
    """Returns a POSIX UTC timestamp."""
    return datetime.now(timezone.utc).timestamp()


class JsonCache:
    """
    Creates a persistent JSON based cache.
    Intended to be performant relative to a potentially slow API, not relative to built in lru_cache or similar.
    N.B. Rules for max size and max age are enforced when the file is saved, but the cache object may exceed limits while it is live in memory.
    """
    
    def __init__(self, cache_folder_path: Path = None, app_name: str = None, max_size: int = 0, max_age: int = 0, force_update: bool = False, cache_file_name: str = None) -> None:        
        """
        Create a persistent JSON cache for a function.

        Keyword Arguments:
         - cache_folder_path: the path to the folder in which the cache file is to be stored
         - app_name: the name of the app with which the cache file is associated. If cache_folder_path is not provided, this will be used to create a folder.
         - max_size: the maximum number of items the cache can store. 0 disables size checking. (default = 0)
         - max_age: the maximum age in seconds after which a cahced value must be replaced. 0 disables age checking. (default = 0)  
         - force_update: if set to True, fresh calls will be made regardless of cached status. (default = False)
         - cache_file_name: a name for the cache file. If none is provided, the file will be named for the function being memoized.
        """
        self.cache_folder_path = cache_folder_path
        self.app_name = app_name
        self.max_size = max_size
        self.max_age = max_age
        self.force_update = force_update
        self.cache_file_name = cache_file_name
        # constructed attributes
        self.cache: dict = {}
        if self.cach_folder_path is None:
            self.cach_folder_path = self._build_cache_folder_path()

    def _build_cache_folder_path(self):
        if self.app_name is None:
            logging.warn("Memoizing functions anonymously is not recommended. Please provide values for app_name or cache_folder_path to avoid collisions.")
            self.cach_folder_path = Path(AppDirs().user_cache_dir) / "json_memoize"
        else:
            self.cach_folder_path = Path(AppDirs(appname=self.app_name).user_cache_dir)


    def memoize(self, func=None):
        if func is None:
            return partial()
        def cache_wrapper(*args, **kwargs):
            for arg in [*args, *kwargs.keys(), *kwargs.values()]:
                _warn_if_repr(arg)
            call_string = f"{args}, {kwargs}"
            if call_string not in self.cache:
                self.store(call_string, func(*args, **kwargs))
                logging.info("%s cached", call_string)
            return self.retrieve(call_string)
        return cache_wrapper
        
    def store(self, call: str, response: Any) -> None:
        """Stores the supplied call and response in the cache."""        
        self.cache[call] = (response, make_timestamp())

    def retrieve(self, call: str) -> Any:
        """Returns the response value of the supplied cached call."""
        return self.cache[call][0]

    def _purge_expired(self) -> None:
        """Deletes all entries older than max_age"""
        if not self.max_age:
            return
        old_calls = [call for call in self.cache if self._age_check(call) > self.max_age]
        for call in old_calls:
            self.cache.pop(call)

    def _age_check(self, call: str) -> float:
        """Returns the age in seconds of the supplied call in the cache."""
        return make_timestamp() - self.cache[call][-1]
    
    def _is_current(self, call: str) -> bool:
        """
        Returns True if the supplied call is current in the cache.
        If force_update is set to True, always returns False. If max_age is 0, always returns True.
        """
        if self.force_update:
            return False
        if not self.max_age:
            return True
        return self._age_check(call) < self.max_age

    def _purge_n_oldest(self, count:int = 1) -> None:
        """Deletes the oldest n entry in the cache."""
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[-1][-1])
        # Entries in the cache are stored in the form {call: (response, timestamp)}
        # so x[-1][-1] grabs the entry's timestamp
        for entry in sorted_entries[:count]:
            self.cache.pop(entry[0])
    
    def _cull_to_size(self) -> None:
        """Determines if max_size has been exceeded, and if so deletes the oldest entries until the size of the cache is complient."""
        if not self.max_size:
            return
        if len(self.cache) > self.max_size:
            self._purge_n_oldest(len(self.cache) - self.max_size)
    
    def write_file(self) -> None:
        if not self.cache_file_path.parent.exists():
            self.cache_file_path.parent.mkdir(parents=True)
        with open(self.cache_file_path, "w") as cache_file:
            json.dump(self.cache, cache_file)

    def read_file(self) -> None:
        """Opens the associated cache file, and loads the file's contents to the cache dict."""
        if not self.cache_file_path.exists():
            self.cache = dict()
            return
        with open(self.cache_file_path, "r") as cache_file:
            contents = cache_file.read()
            if contents:
                self.cache = json.loads(contents)
            else:
                self.cache = dict()

    def __contains__(self, item):
        return item in self.cache and self._is_current(item)

    def __len__(self):
        return len(self.cache)

    def __repr__(self) -> str:
        return f"<JsonCache Object {hex(id(self))} storing {len(self)} items>"

    def __str__(self) -> str:
        return str(self.cache)

    def __enter__(self):
        self.read_file()
        return self
        
    def __exit__(self, *args, **kwargs):
        self._purge_expired()
        self._cull_to_size()
        self.write_file()



"""
cache_file_name = self.cache_file_name or f"{func.__name__}_cache"
cache_file_path = Path(self.cach_folder_path) / cache_file_name
"""