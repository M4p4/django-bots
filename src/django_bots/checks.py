"""System checks for django-bots settings and settings left over from django-user-agents."""

from __future__ import annotations

import re
import warnings
from collections.abc import Sequence
from difflib import get_close_matches
from inspect import isclass
from typing import Any, TypeGuard

from crawleruseragents import CRAWLER_USER_AGENTS_DATA
from django.apps import AppConfig, apps
from django.conf import settings
from django.core.checks import CheckMessage, Error, Warning
from django.utils.module_loading import import_string

from django_bots.ai import ai_bots
from django_bots.conf import BotsSettings, bots_settings

__all__ = [
    "check_ai_allow",
    "check_ai_block_status",
    "check_ai_block_view",
    "check_crawler_extra",
    "check_crawler_ignore",
    "check_django_user_agents_installed",
    "check_list_settings",
    "check_ua_cache_size",
    "check_unknown_settings",
    "check_user_agents_cache",
]

LIST_SETTINGS = (
    "CRAWLER_EXTRA",
    "CRAWLER_IGNORE",
    "AI_ALLOW",
    "AI_EXTRA",
    "AI_BLOCK_EXEMPT_PATHS",
)


def _is_string_list(value: object) -> TypeGuard[Sequence[str]]:
    return isinstance(value, (list, tuple)) and all(
        isinstance(item, str) and item for item in value
    )


def _valid_list(name: str) -> Sequence[str] | None:
    value: object = getattr(bots_settings, name)
    return value if _is_string_list(value) else None


def check_user_agents_cache(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    if not hasattr(settings, "USER_AGENTS_CACHE"):
        return []
    return [
        Warning(
            "USER_AGENTS_CACHE is set, but django-bots doesn't use Django's cache framework.",
            hint="Remove the setting. Parsed user agents are cached in process, sized by BOTS_UA_CACHE_SIZE.",
            id="django_bots.W001",
        )
    ]


def check_django_user_agents_installed(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    if not apps.is_installed("django_user_agents"):
        return []
    return [
        Error(
            "django_user_agents and django_bots are both in INSTALLED_APPS.",
            hint="Remove django_user_agents. Both apps provide the user_agents template library.",
            id="django_bots.E001",
        )
    ]


def check_ai_block_view(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    path = bots_settings.AI_BLOCK_VIEW
    if path is None:
        return []
    try:
        view = import_string(path)
    except ImportError as error:
        problem = str(error)
    else:
        if not callable(view):
            problem = f"{path!r} is not callable."
        elif isclass(view):
            problem = f"{path!r} is a class. Point it at a name set to its as_view()."
        else:
            return []
    return [
        Error(
            f"BOTS_AI_BLOCK_VIEW can't be used: {problem}",
            hint="Set it to the dotted path of a view, or to None for the default response.",
            id="django_bots.E002",
        )
    ]


def _list_hint(value: object) -> str:
    if isinstance(value, str) and value:
        return f"Wrap the value in a list: [{value!r}]."
    return "Use a list of non-empty strings, or [] for none."


def check_list_settings(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    return [
        Error(
            f"BOTS_{name} must be a list of non-empty strings, not {value!r}.",
            hint=_list_hint(value),
            id="django_bots.E003",
        )
        for name in LIST_SETTINGS
        if _valid_list(name) is None
        for value in [getattr(bots_settings, name)]
    ]


def check_crawler_extra(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    messages: list[CheckMessage] = []
    for pattern in _valid_list("CRAWLER_EXTRA") or ():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                # Patterns are joined into one regex, so compile each one in second place.
                re.compile(f"(?!)|{pattern}")
        except (re.error, DeprecationWarning) as error:
            messages.append(
                Error(
                    f"BOTS_CRAWLER_EXTRA pattern {pattern!r} isn't a valid regex: {error}",
                    hint="Patterns are joined into one case-insensitive regex, so leave out inline flags like (?i).",
                    id="django_bots.E004",
                )
            )
    return messages


def check_ua_cache_size(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    size: object = bots_settings.UA_CACHE_SIZE
    if isinstance(size, int) and not isinstance(size, bool) and size >= 0:
        return []
    return [
        Error(
            f"BOTS_UA_CACHE_SIZE must be an integer of 0 or more, not {size!r}.",
            hint="Set it to 0 to turn the cache off.",
            id="django_bots.E005",
        )
    ]


def check_ai_block_status(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    status: object = bots_settings.AI_BLOCK_STATUS
    if (
        not isinstance(status, int)
        or isinstance(status, bool)
        or not 100 <= status <= 599
    ):
        return [
            Error(
                f"BOTS_AI_BLOCK_STATUS must be an HTTP status code from 100 to 599, not {status!r}.",
                id="django_bots.E006",
            )
        ]
    if status < 400:
        return [
            Warning(
                f"BOTS_AI_BLOCK_STATUS is {status}, so blocked requests don't get an error status.",
                hint="Use a 4xx status such as 403 or 404.",
                id="django_bots.W002",
            )
        ]
    return []


def check_unknown_settings(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    known = [name for name in vars(BotsSettings) if name.isupper()]
    messages: list[CheckMessage] = []
    for name in dir(settings):
        if not name.startswith("BOTS_") or name[5:] in known:
            continue
        matches = get_close_matches(name[5:], known, n=1)
        messages.append(
            Warning(
                f"{name} isn't a django-bots setting.",
                hint=f"Did you mean BOTS_{matches[0]}?" if matches else "Remove it.",
                id="django_bots.W003",
            )
        )
    return messages


def check_ai_allow(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    names = {name.lower() for name in [*ai_bots(), *(_valid_list("AI_EXTRA") or ())]}
    return [
        Warning(
            f"BOTS_AI_ALLOW name {name!r} isn't in the AI bot list, so it has no effect.",
            hint="Use a name as it appears in django_bots.ai.ai_bots() or BOTS_AI_EXTRA.",
            id="django_bots.W004",
        )
        for name in _valid_list("AI_ALLOW") or ()
        if name.lower() not in names
    ]


def check_crawler_ignore(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    patterns = {entry["pattern"] for entry in CRAWLER_USER_AGENTS_DATA}
    return [
        Warning(
            f"BOTS_CRAWLER_IGNORE entry {pattern!r} isn't a crawler-user-agents pattern, so it has no effect.",
            hint="Copy the pattern exactly as it's written in the crawler-user-agents list.",
            id="django_bots.W005",
        )
        for pattern in _valid_list("CRAWLER_IGNORE") or ()
        if pattern not in patterns
    ]
