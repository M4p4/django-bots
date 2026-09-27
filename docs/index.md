# django-bots

User-agent parsing, crawler detection and AI bot blocking for Django.

django-bots adds `request.user_agent` to every request with the browser, operating
system and device. It tells you whether a request comes from a crawler or an AI bot, and
can keep AI bots out with a robots.txt view and an opt-in middleware.

Upgrading from django-user-agents only takes new app, middleware and import paths.
The `request.user_agent` attributes, the helpers and the `user_agents` template filters
work the same way. See [Migrating from django-user-agents](migration.md).

## Quickstart

Install the package:

```console
$ pip install django-bots
```

Add the app and the middleware to your settings:

```python
INSTALLED_APPS = [
    # ...
    "django_bots",
]

MIDDLEWARE = [
    # ...
    "django_bots.middleware.UserAgentMiddleware",
]
```

Read the parsed user agent in a view:

```python
def home(request):
    ua = request.user_agent
    if ua.is_ai_bot:
        logger.info("AI bot: %s", ua.ai_bot)
    elif ua.is_crawler:
        ...
    elif ua.is_mobile:
        ...
```

Or in a template:

```django
{% load bots %}

{% if not request|is_bot %}
  <script src="/analytics.js"></script>
{% endif %}
```

Serve a robots.txt that disallows every AI bot:

```python
from django.urls import path

from django_bots.views import robots_txt

urlpatterns = [
    path("robots.txt", robots_txt),
    # ...
]
```

To refuse AI bots with a 403 instead of only asking, see
[Blocking AI bots](ai-bots.md#blocking-ai-bots).

```{toctree}
:maxdepth: 2
:caption: Guide

installation
user-agents
crawlers
ai-bots
migration
limits
```

```{toctree}
:maxdepth: 2
:caption: Reference

settings
templates
api
```

```{toctree}
:maxdepth: 1
:caption: Project

contributing
changelog
```
