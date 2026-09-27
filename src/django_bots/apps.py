from __future__ import annotations

from django.apps import AppConfig
from django.core.checks import Tags, register

from django_bots.checks import (
    check_django_user_agents_installed,
    check_user_agents_cache,
)


class DjangoBotsConfig(AppConfig):
    name = "django_bots"
    verbose_name = "Bots"

    def ready(self) -> None:
        register(check_user_agents_cache, Tags.compatibility)
        register(check_django_user_agents_installed, Tags.compatibility)
