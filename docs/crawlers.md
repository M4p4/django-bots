# Crawler detection

## Checking a request

With the [middleware](user-agents.md#in-views) installed, `request.user_agent.is_crawler`
tells you whether the request comes from a crawler:

```python
def home(request):
    if request.user_agent.is_crawler:
        ...
```

In templates, load the `bots` library and use the `is_crawler`
[filter](templates.md#bots-filters):

```django
{% load bots %}

{% if not request|is_crawler %}
  <script src="/analytics.js"></script>
{% endif %}
```

To check a string without a request, call `django_bots.crawlers.is_crawler()`:

```pycon
>>> from django_bots.crawlers import is_crawler
>>> is_crawler("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
True
>>> is_crawler("python-requests/2.32.3")
True
```

`is_crawler` covers search engines, SEO tools, uptime monitors, feed readers and HTTP
libraries such as python-requests and curl. `is_bot` is true for every crawler, too.

## Where the patterns come from

The patterns come from
[crawler-user-agents](https://github.com/monperrus/crawler-user-agents), installed as
a dependency. It holds about 1,500 regular expressions. Upgrading the package brings
new patterns without a django-bots release:

```console
$ pip install --upgrade crawler-user-agents
```

On first use, the patterns are compiled into one case-insensitive regular expression.
Results are cached per user-agent string, in the same kind of in-process cache as
parsing, sized by `BOTS_UA_CACHE_SIZE` (see [Caching](user-agents.md#caching)).

## Adding and removing patterns

`BOTS_CRAWLER_EXTRA` adds regular expressions, for example for an in-house tool:

```python
BOTS_CRAWLER_EXTRA = [r"^acme-link-checker/"]
```

`BOTS_CRAWLER_IGNORE` removes patterns from the list, for example to treat your uptime
monitor as a normal client:

```python
BOTS_CRAWLER_IGNORE = ["UptimeRobot"]
```

Each entry must match a pattern exactly as it's written in
[crawler-user-agents.json](https://github.com/monperrus/crawler-user-agents/blob/master/crawler-user-agents.json),
backslashes included. `django_bots.crawlers.crawler_patterns()` returns the list in
use, after both settings, so you can check the result:

```pycon
>>> from django_bots.crawlers import crawler_patterns
>>> "UptimeRobot" in crawler_patterns()
False
```
