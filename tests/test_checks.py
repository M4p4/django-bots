from __future__ import annotations

from django.apps import apps
from django.core.checks import Error, Warning, run_checks
from django.test import override_settings


def test_no_messages_by_default():
    result = run_checks()

    assert result == []


def test_user_agents_cache_warns():
    with override_settings(USER_AGENTS_CACHE="default"):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.W001"]
    assert isinstance(result[0], Warning)


def test_django_user_agents_installed_errors(monkeypatch):
    real_is_installed = apps.is_installed
    monkeypatch.setattr(
        apps,
        "is_installed",
        lambda name: name == "django_user_agents" or real_is_installed(name),
    )

    result = run_checks()

    assert [message.id for message in result] == ["django_bots.E001"]
    assert isinstance(result[0], Error)
