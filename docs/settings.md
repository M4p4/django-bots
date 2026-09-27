# Settings

All settings are optional. The [system checks](#system-checks) report values
django-bots can't use when you run `manage.py check` or start the server.

## `BOTS_UA_CACHE_SIZE`

Default: `2048`

How many parsed user agents, crawler checks and AI bot checks each worker process
keeps in its least-recently-used caches. It must be an integer. Set it to `0` to turn
the cache off. See
[Caching](user-agents.md#caching).

## `BOTS_CRAWLER_EXTRA`

Default: `[]`

Regular expressions to treat as crawlers, on top of the crawler-user-agents list.
They're joined into one regex and matched case-insensitively anywhere in the
user-agent string, so leave out inline flags like `(?i)`. See
[Adding and removing patterns](crawlers.md#adding-and-removing-patterns).

## `BOTS_CRAWLER_IGNORE`

Default: `[]`

Patterns to remove from the crawler-user-agents list. Each entry must match a pattern
exactly as it's written in the list.

## `BOTS_AI_ALLOW`

Default: `[]`

AI bot names to remove from the list, compared case-insensitively. A name also removes
its spellings with a version, such as `Name/1.0`. They're neither
detected nor listed in the robots.txt rules. See
[Allowing and adding bots](ai-bots.md#allowing-and-adding-bots).

## `BOTS_AI_EXTRA`

Default: `[]`

Extra AI bot names, matched the same way as the bundled ones.

## `BOTS_AI_BLOCK_CATEGORIES`

Default: `["training", "search", "assistant"]`

[AI bot categories](ai-bots.md#categories) that `AIBotBlockMiddleware` blocks, from
`training`, `search`, `assistant` and `agent`. The system check `django_bots.E007`
reports an unknown category. See
[Choosing what to block](ai-bots.md#choosing-what-to-block).

## `BOTS_AI_BLOCK_STATUS`

Default: `403`

Status code of the response `AIBotBlockMiddleware` sends to AI bots, from 100 to 599.
See
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

## System checks

Every list setting must be a list or tuple of non-empty strings. A plain string would
be read one character at a time.

| ID | Reports |
|---|---|
| `django_bots.E001` | `django_user_agents` installed next to `django_bots` |
| `django_bots.E002` | a `BOTS_AI_BLOCK_VIEW` that can't be imported, isn't callable or is a class |
| `django_bots.E003` | a list setting that isn't a list of non-empty strings |
| `django_bots.E004` | a `BOTS_CRAWLER_EXTRA` pattern that isn't a valid regex |
| `django_bots.E005` | a `BOTS_UA_CACHE_SIZE` that isn't an integer of 0 or more |
| `django_bots.E006` | a `BOTS_AI_BLOCK_STATUS` that isn't a status code from 100 to 599 |
| `django_bots.E007` | a `BOTS_AI_BLOCK_CATEGORIES` entry that isn't a category |
| `django_bots.W001` | `USER_AGENTS_CACHE`, which is ignored |
| `django_bots.W002` | a `BOTS_AI_BLOCK_STATUS` below 400, which tells bots the request worked |
| `django_bots.W003` | a `BOTS_*` setting django-bots doesn't know, usually a typo |
| `django_bots.W004` | a `BOTS_AI_ALLOW` name that isn't in the AI bot list |
| `django_bots.W005` | a `BOTS_CRAWLER_IGNORE` entry that isn't a crawler-user-agents pattern |
