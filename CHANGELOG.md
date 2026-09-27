# Changelog

## Unreleased

- User-agent parsing with `django_bots.useragent.parse()`, a drop-in for `user_agents.parse()`: the same `browser`, `os` and `device` tuples and `is_*` attributes, backed by ua-parser 1.x with an in-process LRU cache sized by `BOTS_UA_CACHE_SIZE`.
- Project scaffold: package layout, app config and a `django_bots.conf` settings object with defaults for every `BOTS_*` setting.
- Documentation site built with Sphinx, Furo and MyST, ready for Read the Docs.
- CI on GitHub Actions: linting, the full test matrix, a 100% coverage gate, package build and docs build.
