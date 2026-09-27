"""Detect AI bots by user-agent string.

The bot list is vendored from `ai.robots.txt
<https://github.com/ai-robots-txt/ai.robots.txt>`_, copyright (c) 2024
ai.robots.txt, released under the MIT license.

Each name matches case-insensitively at word boundaries in the user-agent string,
after URLs (with or without a scheme) and email addresses are removed from it. Results are cached per string in
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

__all__ = [
    "AI_BOT_CATEGORIES",
    "ai_bot_category",
    "ai_bot_names",
    "ai_bots",
    "categorize",
    "is_ai_bot",
    "match_ai_bot",
    "match_ai_bots",
    "robots_rules",
]

AI_BOT_CATEGORIES = ("training", "search", "assistant", "agent")
"""Every AI bot name is in one of these categories. ``training`` is the fallback."""

FUNCTION_CATEGORIES = {
    "AI Data Scrapers": "training",
    "AI Data Providers": "training",
    "AI Search Crawlers": "search",
    "AI Assistants": "assistant",
    "AI Agents": "agent",
    "AI Coding Agents": "agent",
}


def _read_data(name: str) -> Any:
    return json.loads(files("django_bots").joinpath("data", name).read_text("utf-8"))


@lru_cache(maxsize=1)
def ai_bots() -> dict[str, dict[str, Any]]:
    """Return the vendored ai.robots.txt entries, keyed by bot name."""
    bots: dict[str, dict[str, Any]] = _read_data("ai_robots.json")
    return bots


VERSION_SUFFIX = re.compile(r"[/ ]v?\d+(?:\.\d+)*$", re.I)


def _base_name(name: str) -> str:
    return VERSION_SUFFIX.sub("", name).lower()


@lru_cache(maxsize=1)
def _category_overrides() -> dict[str, str]:
    groups: dict[str, list[str]] = _read_data("ai_categories.json")
    return {name: category for category, names in groups.items() for name in names}


def categorize(name: str, entry: dict[str, Any]) -> str:
    """Return the category of an ai.robots.txt entry.

    Upstream's ``function`` field decides where it's one of a few known labels, and
    the bundled ``ai_categories.json`` covers the rest. Anything else is ``training``.
    """
    override = _category_overrides().get(name)
    if override is not None:
        return override
    return FUNCTION_CATEGORIES.get(entry.get("function", ""), "training")


@lru_cache(maxsize=1)
def _bundled_categories() -> dict[str, str]:
    categories: dict[str, str] = {}
    for name, entry in ai_bots().items():
        categories.setdefault(name.lower(), categorize(name, entry))
    return categories


def ai_bot_category(name: str) -> str | None:
    """Return the category of an AI bot name, or ``None`` for a name that isn't listed.

    Names from ``BOTS_AI_EXTRA`` are ``training``.
    """
    category = _bundled_categories().get(name.lower())
    if category is not None:
        return category
    extra = {extra_name.lower() for extra_name in bots_settings.AI_EXTRA}
    return "training" if name.lower() in extra else None


def ai_bot_names() -> list[str]:
    """Return the AI bot names in use, after ``BOTS_AI_ALLOW`` and ``BOTS_AI_EXTRA``.

    Allowing a name also allows its spellings with a version, such as ``Name/1.0``.
    """
    allow = {name.lower() for name in bots_settings.AI_ALLOW}
    names = [*ai_bots(), *bots_settings.AI_EXTRA]
    return list(
        dict.fromkeys(
            name
            for name in names
            if name.lower() not in allow and _base_name(name) not in allow
        )
    )


# Contact links name the operator, not the bot: "openai.com" would match "OpenAI".
URL_OR_EMAIL = re.compile(
    r"(?:https?://|www\.)[^\s;)]+"
    r"|(?<![\w.+-])[\w.+-]+@[\w.-]+"
    r"|(?<![\w.-])[\w-]+(?:\.[\w-]+)+/[^\s;)]*"
)


@lru_cache(maxsize=1)
def _get_matcher(
    cache_size: int, allow: tuple[str, ...], extra: tuple[str, ...]
) -> Callable[[str], tuple[str, ...]]:
    """Build the matcher, rebuilt whenever one of the settings changes."""
    # Upstream lists some names in two spellings, so the first one is reported.
    names = ai_bot_names()
    lowered = {name.lower() for name in names}
    canonical: dict[str, str] = {}
    for name in names:
        # "Name/1.0" is left to "Name", which matches it too and reports a stable name.
        if _base_name(name) != name.lower() and _base_name(name) in lowered:
            continue
        canonical.setdefault(name.lower(), name)
    # Longest first, so a name wins over a shorter name it starts with.
    alternation = "|".join(map(re.escape, sorted(canonical, key=len, reverse=True)))
    # An empty alternation matches everything, so fall back to a never-matching regex.
    regex = re.compile(rf"\b(?:{alternation})\b" if canonical else "(?!)", re.I)

    def match(ua_string: str) -> tuple[str, ...]:
        found = regex.finditer(URL_OR_EMAIL.sub(" ", ua_string))
        return tuple(dict.fromkeys(canonical[m.group().lower()] for m in found))

    if cache_size > 0:
        return lru_cache(maxsize=cache_size)(match)
    return match


def match_ai_bots(ua_string: str) -> tuple[str, ...]:
    """Return every AI bot name the user-agent string matches, in the order they appear."""
    matcher = _get_matcher(
        bots_settings.UA_CACHE_SIZE,
        tuple(bots_settings.AI_ALLOW),
        tuple(bots_settings.AI_EXTRA),
    )
    return matcher(ua_string[:UA_MAX_LENGTH])


def match_ai_bot(ua_string: str) -> str | None:
    """Return the name of the first AI bot the user-agent string matches, or ``None``."""
    names = match_ai_bots(ua_string)
    return names[0] if names else None


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
