# Contributing

Bug reports and pull requests are welcome on
[GitHub](https://github.com/M4p4/django-bots). For a larger change, open an issue
first so we can agree on the approach.

## Setup

The project uses [uv](https://docs.astral.sh/uv/). Clone the repository and run the
tests:

```console
$ git clone https://github.com/M4p4/django-bots.git
$ cd django-bots
$ uv run pytest
```

`uv run` creates a virtual environment with the test dependencies and Django 5.2 on
first use.

## Checks

Every pull request has to pass the same checks as CI.

[pre-commit](https://pre-commit.com/) runs the linters, formatters and mypy. Install
the hooks once, or run them on every file:

```console
$ uvx --with pre-commit-uv pre-commit install
$ uvx --with pre-commit-uv pre-commit run --all-files
```

[tox](https://tox.wiki/) runs the tests on every supported Python and Django version,
and builds the docs:

```console
$ uvx --with tox-uv tox                   # everything
$ uvx --with tox-uv tox -e py314-django61 # one environment
$ uvx --with tox-uv tox -e docs           # the docs
```

Coverage must stay at 100%, branches included. Tox environments need the matching
Python versions; `uv python install 3.10 3.11 3.12 3.13 3.14` gets them all.

When a change affects users, add a line under `## Unreleased` in `CHANGELOG.md`, and
update the docs page for the feature.

## AI bot data updates

The AI bot list in `src/django_bots/data/` is generated, never edited by hand. To
vendor a release yourself:

```console
$ uv run python scripts/download_ai_robots.py v1.53
```

The `AI robots sync` workflow does this automatically. Every day it compares
`data/VERSIONS.json` with the latest ai.robots.txt release and, when upstream is
newer, it:

1. downloads the new `robots.json` and license,
2. bumps the patch version and adds a changelog entry (or, when `## Unreleased`
   already has entries or the version isn't a release, adds the entry there and
   leaves the version alone),
3. opens or updates a pull request from the `ai-robots-sync` branch, listing the
   added and removed bot names,
4. runs the CI workflow on that branch, so the pull request gets its checks.

Merging the pull request doesn't publish anything. Its description has the tag
commands for the release.

You can also run the workflow by hand from the Actions tab, optionally with a specific
release tag.
