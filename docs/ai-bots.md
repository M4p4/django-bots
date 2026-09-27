# AI bots

## Checking a request

With the [middleware](user-agents.md#in-views) installed, `request.user_agent` tells
you whether the request comes from an AI bot, and which one:

```python
def article(request):
    if request.user_agent.is_ai_bot:
        logger.info("AI bot: %s", request.user_agent.ai_bot)
```

`ai_bot` is the name of the matched entry, for example `"GPTBot"`, or `None`.

In templates, load the `bots` library and use the `is_ai_bot`
[filter](templates.md#bots-filters):

```django
{% load bots %}

{% if request|is_ai_bot %}...{% endif %}
```

To check a string without a request, use `django_bots.ai`:

```pycon
>>> from django_bots.ai import is_ai_bot, match_ai_bot
>>> ua = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"
>>> match_ai_bot(ua)
'GPTBot'
>>> is_ai_bot(ua)
True
```

## Where the list comes from

The list comes from [ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt), a
community-maintained list of AI crawlers, scrapers and assistants. django-bots bundles
the `robots.json` file of one upstream release, so detection works offline and
doesn't change between deploys. `django_bots.DATA_VERSIONS` shows which release is
bundled:

```pycon
>>> import django_bots
>>> django_bots.DATA_VERSIONS["ai_robots_txt"]
'v1.52'
```

`django_bots.ai.ai_bots()` returns the bundled entries, keyed by name. Each entry has
the upstream `operator`, `respect` (whether it follows robots.txt), `function` and
`description` fields. django-bots shows them but doesn't use them for decisions.

## How matching works

Each name matches case-insensitively as a whole word anywhere in the user-agent
string. `GPTBot` matches `...; GPTBot/1.2; ...` but not `xGPTBot`. When several names
match, `ai_bot` is the one that comes first in the string.

URLs and email addresses are removed before matching. They name the operator, not the
bot: GPTBot's user agent links to `openai.com`, which would otherwise match the
separate `OpenAI` entry, and Baidu's search crawler links to a page named
`spider.html`, which would match the `Spider` entry.

Some entries are only tokens for robots.txt, such as `Google-Extended` and
`Applebot-Extended`. No crawler sends them in its user agent, so they never match a
request. They still belong in robots.txt rules.

## `is_bot`

`is_bot` is true for a spider, a crawler or an AI bot:

```python
is_bot = device.family == "Spider" or is_crawler or is_ai_bot
```

In django-user-agents, `is_bot` was true only for a spider device, which missed many
bots. This is the one place where django-bots behaves differently.

## Allowing and adding bots

`BOTS_AI_ALLOW` removes names from the list. Use it for bots you want to keep, for
example the crawler behind ChatGPT's search results:

```python
BOTS_AI_ALLOW = ["OAI-SearchBot"]
```

Names are compared case-insensitively, and the list in use is available from
`django_bots.ai.ai_bot_names()`.

`BOTS_AI_EXTRA` adds names that aren't in ai.robots.txt yet. They match the same way
as the bundled names:

```python
BOTS_AI_EXTRA = ["NewAIBot"]
```

Some entries catch more than you might expect. See [Limits](limits.md#broad-entries).
