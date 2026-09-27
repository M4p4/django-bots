# Settings

All settings are optional.

## `BOTS_UA_CACHE_SIZE`

Default: `2048`

How many parsed user agents, crawler checks and AI bot checks each worker process
keeps in its least-recently-used caches. Set it to `0` to turn the cache off. See [Caching](user-agents.md#caching).

## `BOTS_CRAWLER_EXTRA`

Default: `[]`

Regular expressions to treat as crawlers, on top of the crawler-user-agents list.
They're matched case-insensitively anywhere in the user-agent string. See
[Adding and removing patterns](crawlers.md#adding-and-removing-patterns).

## `BOTS_CRAWLER_IGNORE`

Default: `[]`

Patterns to remove from the crawler-user-agents list. Each entry must match a pattern
exactly as it's written in the list.

## `BOTS_AI_ALLOW`

Default: `[]`

AI bot names to remove from the list, compared case-insensitively. See
[Allowing and adding bots](ai-bots.md#allowing-and-adding-bots).

## `BOTS_AI_EXTRA`

Default: `[]`

Extra AI bot names, matched the same way as the bundled ones.

## Settings from django-user-agents

`USER_AGENTS_CACHE` is ignored. django-bots caches parsed user agents in process
instead of in Django's cache framework. If the setting is still there, the system
check `django_bots.W001` warns about it, so you can remove it.
