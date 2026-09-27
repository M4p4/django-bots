# Migrating from django-user-agents

django-bots keeps the `request.user_agent` attributes, the helpers in `utils` and the
`user_agents` template filters of django-user-agents. Moving a project over takes new
app, middleware and import paths, plus a look at every place that reads `is_bot`.

## Steps

1. Swap the packages:

   ```console
   $ pip uninstall django-user-agents user-agents
   $ pip install django-bots
   ```

   Keep `user-agents` if other code in your project imports it.

2. In `INSTALLED_APPS`, replace `"django_user_agents"` with `"django_bots"`:

   ```python
   INSTALLED_APPS = [
       # ...
       "django_bots",
   ]
   ```

   Both apps provide a `user_agents` template library, so they can't be installed
   together. The system check `django_bots.E001` reports it if you forget to remove
   the old app.

3. In `MIDDLEWARE`, replace the old middleware:

   ```python
   MIDDLEWARE = [
       # ...
       "django_bots.middleware.UserAgentMiddleware",
   ]
   ```

4. Update Python imports:

   | Before | After |
   |---|---|
   | `from django_user_agents.utils import get_user_agent` | `from django_bots.utils import get_user_agent` |
   | `from django_user_agents.utils import get_and_set_user_agent` | `from django_bots.utils import get_and_set_user_agent` |
   | `from user_agents import parse` | `from django_bots.useragent import parse` |
   | `from user_agents.parsers import UserAgent` | `from django_bots.useragent import UserAgent` |

5. Leave your templates alone. `{% load user_agents %}` and the `is_mobile`,
   `is_tablet`, `is_touch_capable`, `is_pc` and `is_bot` filters work as before.

6. Remove the `USER_AGENTS_CACHE` setting. See [Settings](#settings).

7. Check every use of `is_bot`. See the next section.

8. Run `python manage.py check` and your test suite.

## `is_bot` covers more

In django-user-agents, `is_bot` is true only when ua-parser reports a `Spider` device.
Many bots don't get that device family, so they counted as people. In django-bots,
`is_bot` is also true for [crawlers](crawlers.md) and [AI bots](ai-bots.md):

```python
is_bot = device.family == "Spider" or is_crawler or is_ai_bot
```

If `is_bot` hides content, skips analytics or changes caching, expect more requests to
take that path. Clients such as python-requests, curl and uptime monitors now count as
bots too. That's usually what you want.

Some people count as bots, too. The VS Code, Cursor and Trae desktop apps put their
names in the user agent of their built-in browsers, and these names are on the
[AI bot list](limits.md#broad-entries). The Slack desktop app matches a crawler
pattern. `AIBotBlockMiddleware` doesn't block them by default, because these names are
in the [`agent` category](ai-bots.md#categories).

To keep the old behavior in one place, check the device family:

```python
if request.user_agent.device.family == "Spider":
    ...
```

To treat a specific client as a person again, remove its pattern with
[`BOTS_CRAWLER_IGNORE`](settings.md#bots_crawler_ignore) or its name with
[`BOTS_AI_ALLOW`](settings.md#bots_ai_allow).

## Settings

| django-user-agents | django-bots |
|---|---|
| `USER_AGENTS_CACHE` | Remove it. Parsed user agents are cached in each worker process, sized by [`BOTS_UA_CACHE_SIZE`](settings.md#bots_ua_cache_size). |

django-user-agents stored parsed user agents in Django's cache framework. django-bots
keeps them in memory instead, which is faster than a round trip to Redis or memcached
and needs no pickling. While `USER_AGENTS_CACHE` is still set, the system check
`django_bots.W001` reminds you to remove it.

Every other setting is new. See the [settings reference](settings.md).

## FAQ

### Do my templates need changes?

No. The `user_agents` library has the same name and filters. To use the new
`is_crawler` and `is_ai_bot` filters, load `bots` instead, which also includes every
`user_agents` filter.

### My middleware subclass calls `process_request()`. What now?

`UserAgentMiddleware` is a plain new-style middleware, so it has no
`process_request()`. Set the attribute yourself with
`django_bots.utils.get_and_set_user_agent(request)`, or read `request.user_agent` in a
middleware placed after `UserAgentMiddleware`.

### Does parsing give the same results?

The browser, OS and device fields come from ua-parser 1.x, and the `is_mobile`,
`is_tablet`, `is_pc`, `is_touch_capable` and `is_email_client` rules are ported from
user-agents 2.2.0. The test suite runs about 200 real user-agent strings through both
packages and checks that every attribute except `is_bot` matches. The one other
difference is Firefox on Android and Firefox OS tablets, which user-agents reports as
mobile and django-bots as tablets. ua-parser's regex
data changes between releases, so browser and device names for new or rare user
agents can still differ from an older install.

### Can I run both packages during the switch?

Not in the same project, because of the template library clash. Switch in one deploy.
The steps above touch only settings and imports, so the change is small to review.

### Do I have to use the crawler and AI bot features?

No. With only `UserAgentMiddleware` installed, the one visible change is the wider
`is_bot`. robots.txt and blocking stay off until you add the view or
`AIBotBlockMiddleware`.
