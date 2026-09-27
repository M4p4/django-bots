# django-bots

[![PyPI version](https://img.shields.io/pypi/v/django-bots.svg)](https://pypi.org/project/django-bots/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-bots.svg)](https://pypi.org/project/django-bots/)
[![CI](https://github.com/M4p4/django-bots/actions/workflows/main.yml/badge.svg)](https://github.com/M4p4/django-bots/actions/workflows/main.yml)
[![Documentation](https://readthedocs.org/projects/djangobots/badge/?version=stable)](https://djangobots.readthedocs.io/)

More and more of the traffic on a website comes from crawlers, scrapers and AI bots
instead of people. I wrote django-bots to tell them apart in Django, and to keep out
the AI bots I don't want.

django-bots tells you who is on the other end of a request: which browser, operating
system and device, whether it's a crawler, and whether it's an AI bot. It can serve a
robots.txt that disallows AI bots and turn them away with a 403. Each feature is
opt-in, and the package adds no models or migrations.

## Installation

```console
python -m pip install django-bots
```

Add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "django_bots",
]
```

## User agents

Add the middleware, and every request gets a lazily parsed `request.user_agent`:

```python
MIDDLEWARE = [
    ...,
    "django_bots.middleware.UserAgentMiddleware",
]
```

```python
def home(request):
    if request.user_agent.is_mobile:
        ...
    request.user_agent.browser  # Browser(family="Mobile Safari", version=(5, 1), version_string="5.1")
    request.user_agent.os  # OperatingSystem(family="iOS", version=(5, 1), version_string="5.1")
    request.user_agent.device  # Device(family="iPhone", brand="Apple", model="iPhone")
```

Templates get the same checks as filters:

```django
{% load bots %}

{% if request|is_mobile %}
  <a href="/app/">Get the app</a>
{% endif %}
```

Parsing uses [ua-parser](https://github.com/ua-parser/uap-python) 1.x with an
in-process cache, and works for sync and async views.

## Crawlers

`is_crawler` matches the patterns from
[crawler-user-agents](https://github.com/monperrus/crawler-user-agents), which cover
search engines, SEO tools, uptime monitors and HTTP libraries:

```python
if request.user_agent.is_crawler:
    ...
```

```django
{% if not request|is_crawler %}
  <script src="/analytics.js"></script>
{% endif %}
```

## AI bots

`is_ai_bot` and `ai_bot` match the list from
[ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt), which is bundled with
the package:

```python
if request.user_agent.is_ai_bot:
    logger.info("AI bot: %s", request.user_agent.ai_bot)  # "GPTBot"
```

Serve a robots.txt that disallows every AI bot:

```python
from django.urls import path

from django_bots.views import robots_txt

urlpatterns = [
    path("robots.txt", robots_txt),
]
```

robots.txt only asks. To refuse AI bots outright, add the blocking middleware near
the top of `MIDDLEWARE`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_bots.middleware.AIBotBlockMiddleware",
    ...,
]
```

`BOTS_AI_ALLOW` keeps the bots you want, for both robots.txt and the middleware:

```python
BOTS_AI_ALLOW = ["OAI-SearchBot"]
```

A daily workflow checks for new ai.robots.txt releases, and data updates ship as patch
releases.

## Upgrading from django-user-agents

The `request.user_agent` attributes, the `django_bots.utils` helpers and the
`user_agents` template filters work the same way as in django-user-agents, so
upgrading comes down to new app, middleware and import paths. One thing behaves
differently: `is_bot` is also true for crawlers and AI bots. The
[migration guide](https://djangobots.readthedocs.io/en/stable/migration.html) walks
through each step.

## Compatibility

| Python | Django |
|---|---|
| 3.10, 3.11 | 5.2 |
| 3.12, 3.13, 3.14 | 5.2, 6.0, 6.1 |

## Data sources and licenses

django-bots is released under the MIT license. It uses:

- [ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt) (MIT), bundled in
  `django_bots/data/` with its license
- [crawler-user-agents](https://github.com/monperrus/crawler-user-agents) (MIT),
  installed as a dependency
- [ua-parser](https://github.com/ua-parser/uap-python) (Apache-2.0), installed as a
  dependency
- the device detection rules of
  [user-agents](https://github.com/selwin/python-user-agents) (MIT), ported into
  `django_bots/useragent.py`

`django_bots.DATA_VERSIONS` shows which versions are in use.

## Documentation

The full documentation is at [djangobots.readthedocs.io](https://djangobots.readthedocs.io/):

- [User agents](https://djangobots.readthedocs.io/en/stable/user-agents.html)
- [Crawler detection](https://djangobots.readthedocs.io/en/stable/crawlers.html)
- [AI bots](https://djangobots.readthedocs.io/en/stable/ai-bots.html)
- [Settings](https://djangobots.readthedocs.io/en/stable/settings.html)
- [Limits](https://djangobots.readthedocs.io/en/stable/limits.html)
- [Contributing](https://djangobots.readthedocs.io/en/stable/contributing.html)
