"""Detect crawlers by user-agent string.

The patterns come from the `crawler-user-agents
<https://github.com/monperrus/crawler-user-agents>`_ package. They're compiled into
one case-insensitive regex on first use, and results are cached per user-agent
string in an LRU of ``BOTS_UA_CACHE_SIZE`` entries.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache

from crawleruseragents import CRAWLER_USER_AGENTS_DATA

from django_bots.conf import UA_MAX_LENGTH, bots_settings

__all__ = ["crawler_patterns", "is_crawler"]


def crawler_patterns() -> list[str]:
    """Return the crawler patterns in use, after ``BOTS_CRAWLER_IGNORE`` and ``BOTS_CRAWLER_EXTRA``."""
    ignore = set(bots_settings.CRAWLER_IGNORE)
    patterns = [
        entry["pattern"]
        for entry in CRAWLER_USER_AGENTS_DATA
        if entry["pattern"] not in ignore
    ]
    return [*patterns, *bots_settings.CRAWLER_EXTRA]


@lru_cache(maxsize=1)
def _get_matcher(
    cache_size: int, extra: tuple[str, ...], ignore: tuple[str, ...]
) -> Callable[[str], bool]:
    """Build the matcher, rebuilt whenever one of the settings changes."""
    # An empty alternation matches everything, so fall back to a never-matching regex.
    regex = re.compile("|".join(crawler_patterns()) or "(?!)", re.IGNORECASE)

    def match(ua_string: str) -> bool:
        return regex.search(ua_string) is not None

    if cache_size > 0:
        return lru_cache(maxsize=cache_size)(match)
    return match


def is_crawler(ua_string: str) -> bool:
    """Whether the user-agent string matches a crawler pattern."""
    matcher = _get_matcher(
        bots_settings.UA_CACHE_SIZE,
        tuple(bots_settings.CRAWLER_EXTRA),
        tuple(bots_settings.CRAWLER_IGNORE),
    )
    return matcher(ua_string[:UA_MAX_LENGTH])
