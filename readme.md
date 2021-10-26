# JSON Memoize

## What this is
Are you pulling repetitive information from a slow API? json_memoize may be able to help.

json_memoize is a straightforward tool for persistent memoization, created with API calls in mind. When you attach the included decorator to a function, it will store the arguments passed to that function and the value the function returns in a JSON file. If the function is called with the same arguments, json_memoize will retrieve the return value from the file rather than running the function again.

## What this isn't
json_memoize is intended for light-duty applications. It's not thread safe, so it's not a good fit for large-scale operations. It doesn't do anything to encrypt or obfuscate the data it stores, so it's not the tool for security-sensitive situations. It's intended to be faster than an API call and isn't optimized any further than that, so if you're looking for break-neck speed, this may not be the tool for you. Since it is based around JSON, it expects to be used with data that can be reliably represented with text. If you are passing types with ambiguous string representations, json_memoize probably won't behave reliably.

**Arguments at a glance**
When `@memoize` is invoked, you can pass it a few arguments:
- `max_age` - sets the maximum allowed age in seconds before a cached entry is considered invalid.
- `max_size` - sets the maximum number of entries that can be stored in the cache.
- `force_update` - overwrites cached values with fresh ones.
- `cache_folder_path` - sets the location of the associated .json file.
- `app_name` - if no `cache_folder_path` is provided, `app_name` is used to create a folder in the default user cache folder.
- `cache_file_name` - manually sets the name of the cache file.


## Basic Use
Import and add the decorator `@memoize` to memoize a function.

**Warning:** json_memoize stores arguments passed to memoized functions in a plain text format. Do not pass your API key, or any other sensitive information, to memoized functions.

Here's a slow api call:
```
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```

Add the `@memoize` decorator to memoize it.
```
from json_memoize import memoize

@memoize
def slow_api_call(arg_1:str, arg_2: str) -> str:
    response = requests.get(f"https://wowthistakesforever.slow/arg-1={arg_1}&arg-2={arg_2}")
    return response.text
```
If the function is called again with the same arguments, the resulting value will be retrieved from the cache file without executing the function.

### max_age
If you don't want to keep data that's too old, you can set a max age. 
```
@memoize(max_age=600)
def slow_api_call(arg_1:str, arg_2: str) -> str:
    ...
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
    ...
```
If max_size is set, json_memoize will delete cache entries from oldest to youngest until it meets the specified size limit before it saves the file to disk. As with max_age, the age of an entry is determined by the time at which it was first added to the cache, not when it was most recently used. 
**Note:** The size limit is only enforced when the cache file is being written. While the JsonCache object is live in memory, the limit can be exceeded.

### force_update
If something in your ecosystem has changed and you want to force the cached values to be updated with fresh information, you can do that too.
```
@memoize(force_update=True)
def slow_api_call(arg_1:str, arg_2: str) -> str:
    ...
```
If `force_update` is `True`, all entries in the cache will be overwritten, even if they have not yet reached `max_age`.

## Setting the Cache Folder
To reduce the likelihood of name collisions, json_memoize stores its cache files in named folders. There are multiple ways to specify where this folder is located.

### Automatic folder creation using app_name
If a value is provided for `app_name`, json_memoize will use this value to name a new folder within the operating systems preferred user cache folder. e.g.:

`@memoize(app_name='my_app')` will create a folder structure like ".cache/my_app/"

### Manual cache folder assignment
If a `cache_folder` argument is supplied to the decorator, it will store cache files in that folder. **Note:** if `cache_folder` is supplied, it will overrule `app_name`.

### Default folder location
**Warning:** Not recommended!

If neither `cache_folder` nor `app_name` is provided, json_memoize will use its default folder name, yielding a folder structure like ".cache/json_memoize/"

This is not recommended, as intermingling cache files from multiple apps increases the risk of file name collisions, which could cause apps to behave unpredictably.

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


## Storage and Performance Details

### Storage
When a call is made to a memoized function, json_memoize will generate a string from the passed arguments, and use that string as the key in its internal cache dictionary. The value returned by the call is stored as the associated value. Writing this dict to disk is accomplished using `json.dump()`. Seperate cache files are made for each memoized function.

**Warning:** It is assumed here that @memoize will be invoked in situations where both the arguments and the returned value of a function have consistent, unambiguous string representations. Passing arguments with unreliable string representation will cause the cache to behave unpredictably. json_memoize will log a warning if it detects something that looks like a repr() output that points to a memory address in an incoming argument. Also, once again, do not pass security-relevant information to memoized functions.

### Performance
json_memoize is intended to be performant relative to a slow API call, and has not been optimized further than that. If `max_size` is exceeded, the entries in the dict are sorted so the oldest ones can be dropped. Setting aside hard drive performance, this sorting operation is the most costly step of the process, and it occurs every time the cahce file is saved.
