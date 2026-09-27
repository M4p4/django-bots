# Contributing

This page is not written yet. It fills in as the feature lands.

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
