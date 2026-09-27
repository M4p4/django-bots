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
`ai_bot_category` is its [category](#categories), for example `"training"`.

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

A scheduled job checks for new ai.robots.txt releases every day and opens a pull
request that updates the bundled list. Data-only updates ship as patch releases, so
upgrading django-bots is how you pick up new bots.

`django_bots.ai.ai_bots()` returns the bundled entries, keyed by name. Each entry has
the upstream `operator`, `respect` (whether it follows robots.txt), `function` and
`description` fields. django-bots shows them but doesn't use them for decisions.

## How matching works

Each name matches case-insensitively as a whole word anywhere in the user-agent
string. `GPTBot` matches `...; GPTBot/1.2; ...` but not `xGPTBot`. When several names
match, `ai_bot` is the one that comes first in the string.

Upstream lists a few bots a second time with a version, such as `MistralAI-User` and
`MistralAI-User/1.0`. `ai_bot` reports the name without the version for every version,
so logs and stats group them together.

URLs, including links without `https://` such as `openai.com/bot`, and email addresses
are removed before matching. They name the operator, not the bot: GPTBot's user agent links to `openai.com`, which would otherwise match the
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

## Serving robots.txt

Add the `robots_txt` view to your URLs:

```python
from django.urls import path

from django_bots.views import robots_txt

urlpatterns = [
    path("robots.txt", robots_txt),
    # ...
]
```

It serves one group that disallows every AI bot, as `text/plain` with
`Cache-Control: max-age=86400`:

```text
User-agent: AddSearchBot
User-agent: AgentTimes
...
User-agent: ZanistaBot
Disallow: /
```

Every name in the list gets a line, including the robots.txt-only tokens and names
that upstream lists in two spellings. The view answers `GET` and `HEAD` and returns
405 for other methods.

To add your own rules and a `Sitemap:` line, create a `django_bots/robots.txt`
template in your project that extends the bundled one and fills the `rules` block:

```django
{% extends "django_bots/robots.txt" %}{% block rules %}
User-agent: *
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
{% endblock %}
```

Your project's template directories must come before the app directories, which is
the default when `DIRS` is set and `APP_DIRS` is on. Django lets a template extend the
template of the same name it overrides.

If you already serve robots.txt from your own template, print the rules with the
[`ai_robots_rules` tag](templates.md#ai_robots_rules) instead.

## Categories

Every AI bot is in one of four categories:

| Category | What the bots do | Examples |
|---|---|---|
| `training` | Collect data to train models, or sell it | `GPTBot`, `ClaudeBot`, `CCBot`, `Bytespider` |
| `search` | Index pages for an AI search engine | `OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot` |
| `assistant` | Fetch a page when a person asks a chatbot about it | `ChatGPT-User`, `Claude-User`, `Perplexity-User` |
| `agent` | Browse or act for a person, including coding agents | `ChatGPT Agent`, `Operator`, `Code`, `Cursor`, `Claude-Code` |

Coding agents such as `Code` (GitHub Copilot in VS Code), `Cursor` and `Trae` send the
user agent of their desktop app, so a person using the app's built-in browser matches
too. That's why the middleware doesn't block agents by default (see
[`BOTS_AI_BLOCK_CATEGORIES`](#choosing-what-to-block)).

The category comes from the `function` field in ai.robots.txt where it's one of the
standard labels, and from a list bundled with django-bots for the rest. Anything
unclear is `training`. Names from `BOTS_AI_EXTRA` are `training` too.

```pycon
>>> from django_bots.ai import ai_bot_category
>>> ai_bot_category("GPTBot")
'training'
>>> ai_bot_category("Cursor")
'agent'
```

## Blocking AI bots

robots.txt only asks. To refuse AI bots outright, add `AIBotBlockMiddleware`:

```{warning}
The list blocks more than AI crawlers. With the default settings, the middleware also
refuses `facebookexternalhit` (link previews on Facebook, Messenger and WhatsApp),
`Applebot` (Siri and Spotlight search), `PetalBot` (Huawei's search engine),
`GoogleOther` and any user agent with the word `spider`. See
[Broad entries](limits.md#broad-entries) and allow the ones you need with
[`BOTS_AI_ALLOW`](#allowing-and-adding-bots).
```

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_bots.middleware.AIBotBlockMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # ...
]
```

Put it high in the list, before sessions, authentication and anything else that does
work for a request. It doesn't need `UserAgentMiddleware`: it checks the raw
user-agent string against the same list as `is_ai_bot`, without parsing the browser,
OS and device.

A blocked request gets a plain-text `Forbidden` response with status 403. Change the
status with `BOTS_AI_BLOCK_STATUS`, or render your own response with a view:

```python
BOTS_AI_BLOCK_STATUS = 429
BOTS_AI_BLOCK_VIEW = "myproject.views.ai_bot_blocked"
```

The view gets the request and returns a response. It can be sync or async, and a
`TemplateResponse` is rendered for you. For a class-based view, point the setting at a
name set to its `as_view()`:

```python
# myproject/views.py
class AIBotBlockedView(TemplateView):
    template_name = "ai_bot_blocked.html"


ai_bot_blocked = AIBotBlockedView.as_view()
```

The path is imported once, when the middleware loads, and the system check
`django_bots.E002` reports a path that can't be imported, isn't callable or is a
class.

Requests to `/robots.txt` are never blocked, so bots can still read your rules.
`BOTS_AI_BLOCK_EXEMPT_PATHS` sets the full list of paths to let through. Each path is
compared exactly with `request.path_info`, the path without the prefix of a site
mounted under a subpath:

```python
BOTS_AI_BLOCK_EXEMPT_PATHS = ["/robots.txt", "/llms.txt"]
```

`BOTS_AI_ALLOW` applies to the middleware too, so an allowed bot is neither disallowed
in robots.txt nor blocked.

### Choosing what to block

`BOTS_AI_BLOCK_CATEGORIES` sets the [categories](#categories) the middleware blocks.
The default blocks everything except agents:

```python
BOTS_AI_BLOCK_CATEGORIES = ["training", "search", "assistant"]
```

To block only bots that collect training data, and let AI search and chatbot fetches
through:

```python
BOTS_AI_BLOCK_CATEGORIES = ["training"]
```

Add `"agent"` to block agents as well, including people in the VS Code, Cursor and
Trae built-in browsers. The setting only changes blocking: robots.txt still lists every
bot, and `is_ai_bot` is true for every category.

## Allowing and adding bots

`BOTS_AI_ALLOW` removes names from the list. Use it for bots you want to keep, for
example the crawler behind ChatGPT's search results:

```python
BOTS_AI_ALLOW = ["OAI-SearchBot"]
```

Names are compared case-insensitively, and the list in use is available from
`django_bots.ai.ai_bot_names()`. Allowing a name also allows its spellings with a
version, so `"MistralAI-User"` covers `MistralAI-User/1.0`. Allowed names are also left
out of the robots.txt rules.

`BOTS_AI_EXTRA` adds names that aren't in ai.robots.txt yet. They match the same way
as the bundled names and get a line in the robots.txt rules:

```python
BOTS_AI_EXTRA = ["NewAIBot"]
```

Some entries catch more than you might expect. See [Limits](limits.md#broad-entries).
