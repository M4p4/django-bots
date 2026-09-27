# Settings

All settings are optional.

## `BOTS_UA_CACHE_SIZE`

Default: `2048`

How many parsed user agents each worker process keeps in its least-recently-used
cache. Set it to `0` to turn the cache off. See [Caching](user-agents.md#caching).

## Settings from django-user-agents

`USER_AGENTS_CACHE` is ignored. django-bots caches parsed user agents in process
instead of in Django's cache framework. If the setting is still there, the system
check `django_bots.W001` warns about it, so you can remove it.
