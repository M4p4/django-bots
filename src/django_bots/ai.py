"""Detect AI bots by user-agent string.

The bot list is vendored from `ai.robots.txt
<https://github.com/ai-robots-txt/ai.robots.txt>`_, copyright (c) 2024
ai.robots.txt, released under the MIT license.

Each name matches case-insensitively at word boundaries in the user-agent string,
after URLs and email addresses are removed from it. Results are cached per string in
an LRU of ``BOTS_UA_CACHE_SIZE`` entries.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from functools import lru_cache
from importlib.resources import files
from typing import Any

from django_bots.conf import UA_MAX_LENGTH, bots_settings

__all__ = ["ai_bot_names", "ai_bots", "is_ai_bot", "match_ai_bot", "robots_rules"]


def _read_data(name: str) -> Any:
    return json.loads(files("django_bots").joinpath("data", name).read_text("utf-8"))


@lru_cache(maxsize=1)
def ai_bots() -> dict[str, dict[str, Any]]:
    """Return the vendored ai.robots.txt entries, keyed by bot name."""
    bots: dict[str, dict[str, Any]] = _read_data("ai_robots.json")
    return bots


def ai_bot_names() -> list[str]:
    """Return the AI bot names in use, after ``BOTS_AI_ALLOW`` and ``BOTS_AI_EXTRA``."""
    allow = {name.lower() for name in bots_settings.AI_ALLOW}
    names = [*ai_bots(), *bots_settings.AI_EXTRA]
    return list(dict.fromkeys(name for name in names if name.lower() not in allow))


# Contact links name the operator, not the bot: "openai.com" would match "OpenAI".
URL_OR_EMAIL = re.compile(r"(?:https?://|www\.)[^\s;)]+|(?<![\w.+-])[\w.+-]+@[\w.-]+")


@lru_cache(maxsize=1)
def _get_matcher(
    cache_size: int, allow: tuple[str, ...], extra: tuple[str, ...]
) -> Callable[[str], str | None]:
    """Build the matcher, rebuilt whenever one of the settings changes."""
    # Upstream lists some names in two spellings, so the first one is reported.
    canonical: dict[str, str] = {}
    for name in ai_bot_names():
        canonical.setdefault(name.lower(), name)
    # Longest first, so a name wins over a shorter name it starts with.
    alternation = "|".join(map(re.escape, sorted(canonical, key=len, reverse=True)))
    # An empty alternation matches everything, so fall back to a never-matching regex.
    regex = re.compile(rf"\b(?:{alternation})\b" if canonical else "(?!)", re.I)

    def match(ua_string: str) -> str | None:
        found = regex.search(URL_OR_EMAIL.sub(" ", ua_string))
        return canonical[found.group().lower()] if found else None

    if cache_size > 0:
        return lru_cache(maxsize=cache_size)(match)
    return match


def match_ai_bot(ua_string: str) -> str | None:
    """Return the name of the AI bot the user-agent string matches, or ``None``."""
    matcher = _get_matcher(
        bots_settings.UA_CACHE_SIZE,
        tuple(bots_settings.AI_ALLOW),
        tuple(bots_settings.AI_EXTRA),
    )
    return matcher(ua_string[:UA_MAX_LENGTH])


def is_ai_bot(ua_string: str) -> bool:
    """Whether the user-agent string matches an AI bot."""
    return match_ai_bot(ua_string) is not None


def robots_rules() -> str:
    """Return a robots.txt group that disallows every AI bot in ``ai_bot_names()``.

    Returns an empty string when no names are left.
    """
    names = ai_bot_names()
    if not names:
        return ""
    return "\n".join([*(f"User-agent: {name}" for name in names), "Disallow: /"])
