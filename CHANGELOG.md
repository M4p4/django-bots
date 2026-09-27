# Changelog

## Unreleased

- Fixed `AIBotBlockMiddleware` returning an unrendered `TemplateResponse` from `BOTS_AI_BLOCK_VIEW`, which raised `ContentNotRenderedError`. Block views built on `TemplateView` and other generic views now work.
- The system check `django_bots.E002` reports a `BOTS_AI_BLOCK_VIEW` that points at a class instead of a view, which failed on the first blocked request.

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
