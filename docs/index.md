# django-bots

User-agent parsing, crawler detection and AI bot blocking for Django.

django-bots adds `request.user_agent` to every request with the browser, operating
system and device. It tells you whether a request comes from a crawler or an AI bot, and
can keep AI bots out with a robots.txt view and an opt-in middleware.

Upgrading from django-user-agents only takes new app, middleware and import paths.
The `request.user_agent` attributes, the helpers and the `user_agents` template filters
work the same way. See [Migrating from django-user-agents](migration.md).

The package is in early development and not yet published on PyPI.

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
