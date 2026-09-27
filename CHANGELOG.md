# Changelog

## Unreleased

- `UserAgentMiddleware` sets a lazily parsed `request.user_agent` for sync and async views. `get_user_agent()` and `get_and_set_user_agent()` in `django_bots.utils`, and the `user_agents` template library with the `is_mobile`, `is_tablet`, `is_touch_capable`, `is_pc` and `is_bot` filters, work as in django-user-agents.
- System checks: `django_bots.W001` warns that `USER_AGENTS_CACHE` is ignored, and `django_bots.E001` reports `django_user_agents` installed next to `django_bots`.
- User-agent parsing with `django_bots.useragent.parse()`, a drop-in for `user_agents.parse()`: the same `browser`, `os` and `device` tuples and `is_*` attributes, backed by ua-parser 1.x with an in-process LRU cache sized by `BOTS_UA_CACHE_SIZE`.
- Project scaffold: package layout, app config and a `django_bots.conf` settings object with defaults for every `BOTS_*` setting.
- Documentation site built with Sphinx, Furo and MyST, ready for Read the Docs.
- CI on GitHub Actions: linting, the full test matrix, a 100% coverage gate, package build and docs build.
