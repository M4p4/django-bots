# django-bots

User-agent parsing, crawler detection and AI bot blocking for Django.

django-bots is a maintained drop-in replacement for
[django-user-agents](https://github.com/selwin/django-user_agents). On top of the same
`request.user_agent` API, it tells you whether a request comes from a crawler or an AI
bot, and can keep AI bots out with a robots.txt view and an opt-in middleware.

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
