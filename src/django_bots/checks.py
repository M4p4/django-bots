"""System checks for settings left over from django-user-agents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.checks import CheckMessage, Error, Warning

__all__ = ["check_django_user_agents_installed", "check_user_agents_cache"]


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
