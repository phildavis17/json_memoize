# JSON Memoize

## What is this?
json_memoize is a straightforward tool for light-duty persistent memoization, created with APIs in mind.

## Requirements
TK (python version?)
appdirs????

## Basic Useage
Add the decorator `@memoize` to memoize a function.

**Warning:** json_memoize stores arguments passed to memoized functions in a plain text format. Do not pass your API key, or any other sensitive information, to memoized functions.

Here's a slow api call:
```
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```

Add the `@memoize` decorator to memoize it.
```
@memoize
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```

### max_age
If you don't want to keep data that's too old, you can set a max age. 
```
@memoize(max_age=600)
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```
The age of an entry is determined from the time it was first added to the cache. If the difference between that time and the current time exceeds the `max_age` value, the cached value will be overwritten with a fresh one. Entries that have exceeded `max_age` will not be written to disk. If `max_age` is not set, cache entries will not expire.
**Note:** `max_age` is in seconds. Consider creating variables for measures of time that are inconvenient or unclear when written in seconds, e.g.:
```
one_week = 604_800
@memoize(max_age=one_week)
...
```
### max_size
If you don't want to cache too many entries, you can set a maximum number of entries to store.
```
@memoize(max_size=10)
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```
If max_size is set, json_memoize will delete cache entries from oldest to youngest until it meets the specified size limit before it saves the file to disk. As with max_age, the age of an entry is determined by the time at which it was first added to the cache, not when it was most recently used. 
**Note:** The size limit is only enforced when the cache file is being written. While the JsonCache object is live in memory, the limit can be exceeded.

### force_update
If something in your ecosystem has changed and you want to force the cached values to be updated with fresh information, you can do that too.
```
@memoize(force_update=True)
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```
If `force_update` is `True`, all entries in the cache will be overwritten, even if they have not yet reached `max_age`.

## Setting the Cache Folder
To reduce the likelihood of name collisions, json_memoize attempts to store its cache files in named folders. There are ways to specify where this folder is located.

### Automatic folder creation using app_name
If a value is provided for `app_name`, json_memoize will use this value to name a new folder within the operating systems preferred user cache folder. e.g.:

`@memoize(app_name='my_app')` will create a folder structure like ".cache/my_app/"

### Manual cache folder assignment
If a `cache_folder` argument is supplied to the decorator, it will store cache files in that folder. **Note:** if `cache_folder` is supplied, it will overrule `app_name`.

### Default folder location
**Warning:** Not recommended

If neither `cache_folder` nor `app_name` is provided, json_memoize will attempt to create a folder using the name of the file in which the decorator has been invoked. e.g.:

using `@memozie` in a file called "slow_apis.py" will create a folder structure like ".cache/slow_apis/"

If no file name can be determined, json_memoize will use a default folder name, like ".cache/default/"

This is not recommended, as the name of the file is not a reliable source of meaningful information. Intermingling cache files from multiple apps risks name collisions, which could cause apps to behave unpredictably. 

## Naming Cache Files
By default, json_memoize will create each cache file using the name of the function being memoized, e.g.:

```
@memoize
def slow_api_call():
... 
```

This will create a file called "slow_api_call_cahce.json".

### Setting a custom file name with cahce_file_name
If a value is provided for `cache_file_name`, json_memoize will instead use this value to name the cache file.


## Arguments Should 
json_memoize creates a seperate cache file for each decorated function. These files are json representations of python dictionaries in which each entry's key is a string representation of the arguments passed to the memoized function, and the value is whatever that function returns. 

**Warning:** Passing arguments with unreliable string representation will cause the cache to behave unpredictably. json_memoize will log a warning if it detects something that looks like a repr() output in an incoming argument. 

