# Changelog

## Unreleased

- A README with a short example for each feature, a step-by-step guide for upgrading from django-user-agents, a quickstart and a contributing guide in the docs.
- A daily GitHub Actions workflow checks for new ai.robots.txt releases and opens a pull request that updates the bundled AI bot list, bumps the patch version and lists the added and removed bots.
- `django_bots.middleware.AIBotBlockMiddleware` answers AI bots with a 403, for sync and async requests. `BOTS_AI_BLOCK_STATUS` changes the status, `BOTS_AI_BLOCK_VIEW` renders your own response, and `BOTS_AI_BLOCK_EXEMPT_PATHS` lets paths through (`/robots.txt` by default). The system check `django_bots.E002` reports a `BOTS_AI_BLOCK_VIEW` that can't be imported.
- A `django_bots.views.robots_txt` view that disallows every AI bot, rendered from the `django_bots/robots.txt` template with a `rules` block for your own rules. The `ai_robots_rules` tag in the `bots` library prints the same rules into your own template, and `django_bots.ai.robots_rules()` returns them as a string.
- AI bot detection based on ai.robots.txt v1.52, bundled with the package: `django_bots.ai.is_ai_bot()` and `match_ai_bot()`, `request.user_agent.is_ai_bot` and `ai_bot`, and the `is_ai_bot` filter in the `bots` library. `BOTS_AI_ALLOW` removes names and `BOTS_AI_EXTRA` adds them. `django_bots.DATA_VERSIONS` lists the bundled and installed data versions.
- `is_bot` is now also true for crawlers and AI bots, not only for spider devices. This is the one behavior difference from django-user-agents.
- Crawler detection based on crawler-user-agents: `django_bots.crawlers.is_crawler()`, `request.user_agent.is_crawler`, and a new `bots` template library with the `is_crawler` filter and every `user_agents` filter. `BOTS_CRAWLER_EXTRA` adds patterns and `BOTS_CRAWLER_IGNORE` removes them.
- `UserAgentMiddleware` sets a lazily parsed `request.user_agent` for sync and async views. `get_user_agent()` and `get_and_set_user_agent()` in `django_bots.utils`, and the `user_agents` template library with the `is_mobile`, `is_tablet`, `is_touch_capable`, `is_pc` and `is_bot` filters, work as in django-user-agents.
- System checks: `django_bots.W001` warns that `USER_AGENTS_CACHE` is ignored, and `django_bots.E001` reports `django_user_agents` installed next to `django_bots`.
- User-agent parsing with `django_bots.useragent.parse()`, with the same API as `user_agents.parse()`: the same `browser`, `os` and `device` tuples and `is_*` attributes, backed by ua-parser 1.x with an in-process LRU cache sized by `BOTS_UA_CACHE_SIZE`.
- Project scaffold: package layout, app config and a `django_bots.conf` settings object with defaults for every `BOTS_*` setting.
- Documentation site built with Sphinx, Furo and MyST, ready for Read the Docs.
- CI on GitHub Actions: linting, the full test matrix, a 100% coverage gate, package build and docs build.
