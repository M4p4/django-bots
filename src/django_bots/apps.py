from __future__ import annotations

from django.apps import AppConfig
from django.core.checks import Tags, register

from django_bots.checks import (
    check_ai_allow,
    check_ai_block_status,
    check_ai_block_view,
    check_crawler_extra,
    check_crawler_ignore,
    check_django_user_agents_installed,
    check_list_settings,
    check_ua_cache_size,
    check_unknown_settings,
    check_user_agents_cache,
)


class DjangoBotsConfig(AppConfig):
    name = "django_bots"
    verbose_name = "Bots"

    def ready(self) -> None:
        register(check_user_agents_cache, Tags.compatibility)
        register(check_django_user_agents_installed, Tags.compatibility)
        register(check_ai_block_view)
        for check in (
            check_list_settings,
            check_crawler_extra,
            check_ua_cache_size,
            check_ai_block_status,
            check_unknown_settings,
            check_ai_allow,
            check_crawler_ignore,
        ):
            register(check)
