# Settings

All settings are optional.

## `BOTS_UA_CACHE_SIZE`

Default: `2048`

How many parsed user agents, crawler checks and AI bot checks each worker process
keeps in its least-recently-used caches. Set it to `0` to turn the cache off. See
[Caching](user-agents.md#caching).

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

AI bot names to remove from the list, compared case-insensitively. They're neither
detected nor listed in the robots.txt rules. See
[Allowing and adding bots](ai-bots.md#allowing-and-adding-bots).

## `BOTS_AI_EXTRA`

Default: `[]`

Extra AI bot names, matched the same way as the bundled ones.

## `BOTS_AI_BLOCK_STATUS`

Default: `403`

Status code of the response `AIBotBlockMiddleware` sends to AI bots. See
[Blocking AI bots](ai-bots.md#blocking-ai-bots).

## `BOTS_AI_BLOCK_VIEW`

Default: `None`

Dotted path to a view that renders the response for blocked requests instead, for
example `"myproject.views.ai_bot_blocked"`. It's imported once, when the middleware
loads. The system check `django_bots.E002` reports a path that can't be imported,
isn't callable or is a class. See [Blocking AI bots](ai-bots.md#blocking-ai-bots).

## `BOTS_AI_BLOCK_EXEMPT_PATHS`

Default: `["/robots.txt"]`

Paths that `AIBotBlockMiddleware` never blocks, compared exactly with
`request.path_info`, which leaves out the prefix of a site mounted under a subpath.
If you set it, keep `/robots.txt` in the list so bots can read your rules.

## Settings from django-user-agents

`USER_AGENTS_CACHE` is ignored. django-bots caches parsed user agents in process
instead of in Django's cache framework. If the setting is still there, the system
check `django_bots.W001` warns about it, so you can remove it.
