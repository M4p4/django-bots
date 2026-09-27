from __future__ import annotations

import pytest
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


@pytest.mark.parametrize(
    "view",
    [None, "tests.test_middleware.block_view", "tests.test_middleware.block_view_cbv"],
)
def test_ai_block_view_valid(view):
    with override_settings(BOTS_AI_BLOCK_VIEW=view):
        result = run_checks()

    assert result == []


@pytest.mark.parametrize(
    "view",
    [
        "tests.test_middleware.missing",
        "missing.module.view",
        "tests.test_middleware.GPTBOT",
        "tests.test_middleware.BlockView",
        "django.http.HttpResponse",
    ],
)
def test_ai_block_view_invalid(view):
    with override_settings(BOTS_AI_BLOCK_VIEW=view):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E002"]
    assert isinstance(result[0], Error)
