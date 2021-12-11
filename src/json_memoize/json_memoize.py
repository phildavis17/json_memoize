# MIT License
# Phil Davis, 2021

import json
import logging

from datetime import datetime, timezone
from functools import partial, wraps
from pathlib import Path
from typing import Any, Callable, Optional

from appdirs import AppDirs

def memoize(
        func: Callable = None,
        max_age: int = 0,
        max_size: int = 0,
        force_update: bool = False,
        app_name: str = None,
        cache_folder_path: Path = None,        
        cache_file_name: str = None        
    ) -> Any:
        if func is None:
            return partial(memoize, cache_folder_path=cache_folder_path, app_name=app_name, cache_file_name=cache_file_name, max_age=max_age, max_size=max_size, force_update=force_update)
        @wraps(func)
        def cache_wrapper(*args, **kwargs):
            cache_folder = _construct_cache_folder_path(cache_folder_path, app_name)
            file_name = cache_file_name or f"{func.__name__}_cache"
            cache_file_path = Path(cache_folder) / file_name
            for arg in [*args, *kwargs.keys(), *kwargs.values()]:
                _warn_if_repr(arg)
                """
                if "__str__" in dir(object)
                """
            call_string = f"{args}, {kwargs}"
            with JsonCache(cache_file_path, max_size=max_size, max_age=max_age, force_update=force_update) as cache:
                if call_string not in cache:
                    cache.store(call_string, func(*args, **kwargs))
                    logging.info("%s cached", call_string)
                return cache.retrieve(call_string)
        return cache_wrapper


def _warn_if_repr(item: Any) -> None:
    """Logs a warning if a call to the supplied item's __str__ returns something that looks like a __repr__ output."""
    str_rep = str(item)
    if "<" in str_rep and ">" in str_rep:
        logging.warn("%s <-- This looks like it might be a repr output. Cache may not behave as expected.", str_rep)


def _construct_cache_folder_path(cache_folder_path: Optional[Path], app_name: Optional[str]) -> Path:
    """
    Uses supplied arguments to construct a Path to a folder.
    If no information is provided, loggs a warning and uses a default value.
    """
    if cache_folder_path is not None and cache_folder_path:
        return Path(cache_folder_path)
    elif app_name is not None and app_name:
        return Path(AppDirs(appname=app_name).user_cache_dir)
    else:
        logging.warn("Caching in default folder is not recommended. Provide app_name or cache_folder_path to avoid collisions.")
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
    
    def __init__(self, cache_file_path: Path, max_size: int = 0, max_age: int = 0, force_update: bool = False) -> None:        
        """
        Allows for persistent memoization of a function using a .json file.

        Keyword Arguments:
         - cache_file_path: a Path object pointing to the associated cache file
         - max_size: the maximum number of items the cache can store. 0 disables size checking. (default = 0)
         - max_age: the maximum age in seconds after which a cahced value must be replaced. 0 disables age checking. (default = 0)  
         - force_update: if set to True, fresh calls will be made regardless of cached status. (default = False)
        """
        self.cache_file_path = cache_file_path
        self.max_size = max_size
        self.max_age = max_age
        self.force_update = force_update
        self.cache: dict = {}
        
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
        # so x[-1][-1] refers to an entry's timestamp
        for entry in sorted_entries[:count]:
            self.cache.pop(entry[0])
    
    def _cull_to_size(self) -> None:
        """Determines if max_size has been exceeded, and if so deletes the oldest entries until the size of the cache is complient."""
        if not self.max_size:
            return
        if len(self.cache) > self.max_size:
            self._purge_n_oldest(len(self.cache) - self.max_size)
    
    def write_file(self) -> None:
        """Writes the contents of the cahce to a json file."""
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
        return f"<JsonCache object at {hex(id(self))} storing {len(self)} items>"

    def __str__(self) -> str:
        return str(self.cache)

    def __enter__(self):
        self.read_file()
        return self
        
    def __exit__(self, *args, **kwargs):
        self._purge_expired()
        self._cull_to_size()
        self.write_file()


class JsonMemoize:
    """
    A class used to establish default values for memoizing functions.
    Arguments supplied here will be used as defaults if no value is supplied to the decorator.
    """
    def __init__(
        self,
        app_name: str = None,
        cache_folder_path: Path = None,        
        cache_file_name: str = None,
        max_age: int = 0,
        max_size: int = 0,
        force_update: bool = False
    ) -> None:
        self.app_name = app_name
        self.cache_folder_path = cache_folder_path
        self.cache_file_name = cache_file_name
        self.max_age = max_age
        self.max_size = max_size
        self.force_update = force_update
        
        #construct a partial of memoize using supplied values
        #passed_args = {k: v for k, v in self.__dict__.items() if v is not None}
        
    def memoize_with_defaults(
        self,
        func: Callable = None,
        max_age: int = None,
        max_size: int = None,
        force_update: bool = None,
        app_name: str = None,
        cache_folder_path: Path = None,
        cache_file_name: str = None,
    ) -> Any:
        """
        Memoize the decorated functions using the default values with which this object was instantiated.
        """
        if max_age is None:
            max_age = self.max_age
        if max_size is None:
            max_size = self.max_size
        if force_update is None:
            force_update = self.force_update
        if app_name is None:
            app_name = self.app_name
        if cache_folder_path is None:
            cache_folder_path = self.cache_folder_path
        if cache_file_name is None:
            cache_file_name = self.cache_file_name

        return memoize(
            func,
            max_age = max_age,
            max_size = max_size,
            force_update = force_update,
            app_name = app_name,
            cache_folder_path = cache_folder_path, 
            cache_file_name = cache_file_name,
        )


