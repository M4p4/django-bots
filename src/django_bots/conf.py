"""Settings for django-bots, each read from Django settings with a default.

Values are looked up on every access, so ``override_settings`` works without any
cache to clear.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from django.conf import settings

__all__ = ["UA_MAX_LENGTH", "bots_settings"]

T = TypeVar("T")

UA_MAX_LENGTH = 512
"""Only this many characters of a user agent are parsed and matched."""


def _get(name: str, default: T) -> T:
    value: T = getattr(settings, f"BOTS_{name}", default)
    return value


class BotsSettings:
    @property
    def UA_CACHE_SIZE(self) -> int:
        """LRU size for parsed user agents and bot checks."""
        return _get("UA_CACHE_SIZE", 2048)

    @property
    def CRAWLER_EXTRA(self) -> Sequence[str]:
        """Extra regex patterns to treat as crawlers."""
        return _get("CRAWLER_EXTRA", ())

    @property
    def CRAWLER_IGNORE(self) -> Sequence[str]:
        """Crawler patterns to leave out of detection."""
        return _get("CRAWLER_IGNORE", ())

    @property
    def AI_ALLOW(self) -> Sequence[str]:
        """AI bot names to leave out of robots.txt rules and blocking."""
        return _get("AI_ALLOW", ())

    @property
    def AI_EXTRA(self) -> Sequence[str]:
        """Extra bot names to treat as AI bots."""
        return _get("AI_EXTRA", ())

    @property
    def AI_BLOCK_CATEGORIES(self) -> Sequence[str]:
        """AI bot categories the blocking middleware blocks."""
        return _get("AI_BLOCK_CATEGORIES", ("training", "search", "assistant"))

    @property
    def AI_BLOCK_STATUS(self) -> int:
        """Status code of the default block response."""
        return _get("AI_BLOCK_STATUS", 403)

    @property
    def AI_BLOCK_VIEW(self) -> str | None:
        """Dotted path to a view that renders the block response instead."""
        return _get("AI_BLOCK_VIEW", None)

    @property
    def AI_BLOCK_EXEMPT_PATHS(self) -> Sequence[str]:
        """Paths the blocking middleware never blocks."""
        return _get("AI_BLOCK_EXEMPT_PATHS", ("/robots.txt",))


bots_settings = BotsSettings()
