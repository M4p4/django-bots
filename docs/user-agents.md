# User agents

## In views

Add the middleware to read the parsed user agent from `request.user_agent`:

```python
MIDDLEWARE = [
    # ...
    "django_bots.middleware.UserAgentMiddleware",
]
```

```python
def home(request):
    if request.user_agent.is_mobile:
        ...
```

The middleware works with sync and async views. It parses the `User-Agent` header the
first time `request.user_agent` is read, so requests that never read it cost nothing.

Without the middleware, the helpers in `django_bots.utils` do the same job:

```python
from django_bots.utils import get_and_set_user_agent, get_user_agent

user_agent = get_user_agent(request)  # parse the header
user_agent = get_and_set_user_agent(request)  # reuse request.user_agent, or set it
```

In templates, use the [filters](templates.md).

## Parsing a string

`django_bots.useragent.parse()` turns a user-agent string into browser, OS and device
details:

```pycon
>>> from django_bots.useragent import parse
>>> ua = parse(
...     "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 "
...     "(KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3"
... )
>>> str(ua)
'iPhone / iOS 5.1 / Mobile Safari 5.1'
>>> ua.is_mobile, ua.is_touch_capable, ua.is_pc
(True, True, False)
```

It also takes bytes, such as a header from an ASGI scope, and decodes them as Latin-1
the way Django does. `None` parses like an empty string.

The API is the same as `user_agents.parse()` from the
[user-agents](https://github.com/selwin/python-user-agents) package, which
django-user-agents is built on.

## Attributes

| Attribute | Example | Meaning |
|---|---|---|
| `ua_string` | `"Mozilla/5.0 (iPhone; ..."` | The string that was parsed |
| `browser` | `Browser(family="Mobile Safari", version=(5, 1), version_string="5.1")` | Browser family and version |
| `os` | `OperatingSystem(family="iOS", version=(5, 1), version_string="5.1")` | Operating system family and version |
| `device` | `Device(family="iPhone", brand="Apple", model="iPhone")` | Device family, brand and model |
| `is_mobile` | `True` | A phone. Tablets are not mobile. |
| `is_tablet` | `False` | A tablet |
| `is_pc` | `False` | A desktop or laptop running Windows, macOS, Linux or ChromeOS |
| `is_touch_capable` | `True` | A device with a touch screen |
| `is_email_client` | `False` | An email client such as Outlook or Thunderbird |
| `is_bot` | `False` | A spider, a crawler or an AI bot (see [`is_bot`](ai-bots.md#is_bot)) |
| `is_crawler` | `False` | Matches a [crawler pattern](crawlers.md) |
| `is_ai_bot` | `False` | Matches an [AI bot](ai-bots.md) |
| `ai_bot` | `None` | Name of the matched AI bot, such as `"GPTBot"` |
| `ai_bot_category` | `None` | [Category](ai-bots.md#categories) of the matched AI bot, such as `"training"` |

`browser`, `os` and `device` are named tuples. Version parts made of digits are
ints, and other parts stay strings, so Windows RT gives `version=("RT",)`.

Three methods return short labels, and `str()` joins them with slashes:

| Method | Example |
|---|---|
| `get_device()` | `"iPhone"`, or `"PC"` when `is_pc` is true |
| `get_os()` | `"iOS 5.1"` |
| `get_browser()` | `"Mobile Safari 5.1"` |

An empty string or `None` parses to `"Other / Other / Other"` rather than raising an
error.

## How parsing works

The browser, OS and device fields come from
[ua-parser](https://github.com/ua-parser/uap-python) 1.x. It uses the fastest backend
that's installed. To speed up parsing, install one of the optional backends:

```console
$ pip install "ua-parser[regex]"   # Rust backend, fastest
$ pip install "ua-parser[re2]"     # google-re2 backend
```

The `is_mobile`, `is_tablet`, `is_pc`, `is_touch_capable` and `is_email_client` rules
are ported from user-agents 2.2.0. A test suite runs about 200 real user-agent strings
through both packages and checks that every attribute matches.

## Caching

Parsed results are cached in process with a least-recently-used cache, keyed by the
user-agent string. `BOTS_UA_CACHE_SIZE` sets how many entries it holds (default
`2048`). Set it to `0` to turn the cache off.

The cache lives in each worker process. django-bots doesn't use Django's cache
framework: a network round trip to Redis or memcached costs more than parsing a
cached string in memory.
