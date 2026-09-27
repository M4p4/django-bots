# Changelog

## Unreleased

## 1.2.0 (2026-09-27)

- AI bots have a category: `training`, `search`, `assistant` or `agent`. It's available as `request.user_agent.ai_bot_category` and `django_bots.ai.ai_bot_category()`.
- `AIBotBlockMiddleware` blocks only the categories in the new `BOTS_AI_BLOCK_CATEGORIES` setting. **The default leaves out `agent`**, so coding and browsing agents such as `Code`, `Cursor`, `Trae`, `Operator` and `ChatGPT Agent` are no longer blocked. Their user agents are the same as those of people using the VS Code, Cursor and Trae built-in browsers, who were blocked before. Set `BOTS_AI_BLOCK_CATEGORIES = ["training", "search", "assistant", "agent"]` to block them as before. `is_ai_bot` and robots.txt are unchanged.
- The system check `django_bots.E007` reports unknown categories in `BOTS_AI_BLOCK_CATEGORIES`.

## 1.1.1 (2026-09-27)

- Fixed the template filters raising `AttributeError` when the `request` variable isn't a request, for example a dict in an email context or an object with a `user_agent` string field. They return `False` like they do without a `request`.
- Links without a scheme, such as `+openai.com/gptbot`, are removed before AI bot matching like `https://` links, so they no longer match the operator's name (here `OpenAI`).
- Firefox on Android tablets (`Android 14; Tablet; ... Firefox/...`) is `is_tablet` instead of `is_mobile`. This differs from django-user-agents, which reports these tablets as mobile.
- `parse()` accepts bytes, such as a header from an ASGI scope, and decodes them as Latin-1 like Django does. It raised `TypeError` before.

## 1.1.0 (2026-09-27)

- New system checks for settings. Errors report list settings that aren't lists of non-empty strings (`django_bots.E003`), invalid `BOTS_CRAWLER_EXTRA` patterns (`E004`), a `BOTS_UA_CACHE_SIZE` that isn't an integer of 0 or more (`E005`) and a `BOTS_AI_BLOCK_STATUS` outside 100 to 599 (`E006`). Before, these broke detection silently or raised on requests. Warnings report a block status below 400 (`W002`), unknown `BOTS_*` settings (`W003`), `BOTS_AI_ALLOW` names that aren't in the list (`W004`) and `BOTS_CRAWLER_IGNORE` entries that match no pattern (`W005`).
- `ai_bot` reports the same name for every version of a bot that upstream also lists with a version. `MistralAI-User/1.0` used to report `"MistralAI-User/1.0"` and `MistralAI-User/1.1` `"MistralAI-User"`; both now report `"MistralAI-User"`. The same applies to `iaskspider` and `Brightbot`. Values logged or stored from `ai_bot` change for these bots.
- `BOTS_AI_ALLOW` also allows a name's spellings with a version, so allowing `MistralAI-User` no longer leaves `MistralAI-User/1.0` blocked and listed in robots.txt.

## 1.0.2 (2026-09-27)

- Fixed `AIBotBlockMiddleware` returning an unrendered `TemplateResponse` from `BOTS_AI_BLOCK_VIEW`, which raised `ContentNotRenderedError`. Block views built on `TemplateView` and other generic views now work.
- The system check `django_bots.E002` reports a `BOTS_AI_BLOCK_VIEW` that points at a class instead of a view, which failed on the first blocked request.
- Fixed `BOTS_AI_BLOCK_EXEMPT_PATHS` for sites mounted under a subpath. Paths are compared with `request.path_info` instead of `request.path`, which includes the prefix, so AI bots were blocked from `/robots.txt` there.
- The default block response sends `Cache-Control: private, no-store`, so shared caches don't serve it to other visitors.
- Fixed the `robots_txt` view returning a 500 in projects without Django's template engine, such as API-only or Jinja2-only projects. It serves the rules as plain text there.

## 1.0.1 (2026-09-27)

- Fixed AI bot matching taking quadratic time on long user agents without spaces. A single `User-Agent` header of a few kilobytes could keep a worker busy for seconds, and `AIBotBlockMiddleware` checks every request.
- Only the first 512 characters of a user agent are parsed and matched. Real user agents are far shorter, and the limit bounds the work for any header.

## 1.0.0 (2026-09-27)

First release.

- User-agent parsing with `django_bots.useragent.parse()`, with the same API as `user_agents.parse()`: the same `browser`, `os` and `device` tuples and `is_*` attributes, backed by ua-parser 1.x with an in-process LRU cache sized by `BOTS_UA_CACHE_SIZE`.
- `UserAgentMiddleware` sets a lazily parsed `request.user_agent` for sync and async views. `get_user_agent()` and `get_and_set_user_agent()` in `django_bots.utils`, and the `user_agents` template library with the `is_mobile`, `is_tablet`, `is_touch_capable`, `is_pc` and `is_bot` filters, work as in django-user-agents.
- Crawler detection based on crawler-user-agents: `django_bots.crawlers.is_crawler()`, `request.user_agent.is_crawler`, and a `bots` template library with the `is_crawler` filter and every `user_agents` filter. `BOTS_CRAWLER_EXTRA` adds patterns and `BOTS_CRAWLER_IGNORE` removes them.
- AI bot detection based on ai.robots.txt v1.52, bundled with the package: `django_bots.ai.is_ai_bot()` and `match_ai_bot()`, `request.user_agent.is_ai_bot` and `ai_bot`, and the `is_ai_bot` filter in the `bots` library. `BOTS_AI_ALLOW` removes names and `BOTS_AI_EXTRA` adds them. `django_bots.DATA_VERSIONS` lists the bundled and installed data versions.
- `is_bot` is true for spider devices, crawlers and AI bots. This is the one behavior difference from django-user-agents, where it only covers spider devices.
- A `django_bots.views.robots_txt` view that disallows every AI bot, rendered from the `django_bots/robots.txt` template with a `rules` block for your own rules. The `ai_robots_rules` tag in the `bots` library prints the same rules into your own template, and `django_bots.ai.robots_rules()` returns them as a string.
- `django_bots.middleware.AIBotBlockMiddleware` answers AI bots with a 403, for sync and async requests. `BOTS_AI_BLOCK_STATUS` changes the status, `BOTS_AI_BLOCK_VIEW` renders your own response, and `BOTS_AI_BLOCK_EXEMPT_PATHS` lets paths through (`/robots.txt` by default).
- System checks: `django_bots.W001` warns that `USER_AGENTS_CACHE` is ignored, `django_bots.E001` reports `django_user_agents` installed next to `django_bots`, and `django_bots.E002` reports a `BOTS_AI_BLOCK_VIEW` that can't be imported.
- Documentation with a quickstart, a guide for upgrading from django-user-agents, and a page on the limits of user-agent based detection.
