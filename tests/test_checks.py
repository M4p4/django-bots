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


@pytest.mark.parametrize(
    "name",
    [
        "BOTS_CRAWLER_EXTRA",
        "BOTS_CRAWLER_IGNORE",
        "BOTS_AI_ALLOW",
        "BOTS_AI_EXTRA",
        "BOTS_AI_BLOCK_EXEMPT_PATHS",
        "BOTS_AI_BLOCK_CATEGORIES",
    ],
)
@pytest.mark.parametrize("value", ["/robots.txt", ["ok", ""], ["ok", 1], {"ok"}, None])
def test_list_setting_invalid(name, value):
    with override_settings(**{name: value}):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E003"]
    assert isinstance(result[0], Error)
    assert name in result[0].msg


@pytest.mark.parametrize(
    ("value", "hint"),
    [
        ("MyBot", "Wrap the value in a list: ['MyBot']."),
        ("", "Use a list of non-empty strings, or [] for none."),
        (None, "Use a list of non-empty strings, or [] for none."),
        (["ok", ""], "Use a list of non-empty strings, or [] for none."),
    ],
)
def test_list_setting_hint(value, hint):
    with override_settings(BOTS_AI_EXTRA=value):
        result = run_checks()

    assert result[0].hint == hint


@pytest.mark.parametrize(
    "settings",
    [
        {"BOTS_CRAWLER_EXTRA": [r"^acme-checker/", "my-monitor"]},
        {"BOTS_CRAWLER_EXTRA": ("my-monitor",)},
        {"BOTS_CRAWLER_IGNORE": ["UptimeRobot"]},
        {"BOTS_AI_ALLOW": ["gptbot", "NewBot"], "BOTS_AI_EXTRA": ["NewBot"]},
        {"BOTS_AI_BLOCK_EXEMPT_PATHS": []},
        {"BOTS_UA_CACHE_SIZE": 0},
        {"BOTS_AI_BLOCK_STATUS": 404},
        {"BOTS_AI_BLOCK_CATEGORIES": ["training", "search", "assistant", "agent"]},
        {"BOTS_AI_BLOCK_CATEGORIES": []},
    ],
)
def test_valid_settings(settings):
    with override_settings(**settings):
        result = run_checks()

    assert result == []


@pytest.mark.parametrize("pattern", ["MyBot(", "a)(b", "(?i)mybot"])
def test_crawler_extra_invalid_regex(pattern):
    with override_settings(BOTS_CRAWLER_EXTRA=["my-monitor", pattern]):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E004"]
    assert isinstance(result[0], Error)
    assert repr(pattern) in result[0].msg


@pytest.mark.parametrize("size", [None, "100", -1, 1.5, True])
def test_ua_cache_size_invalid(size):
    with override_settings(BOTS_UA_CACHE_SIZE=size):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E005"]
    assert isinstance(result[0], Error)


@pytest.mark.parametrize("status", [99, 600, 999, "403", None, True])
def test_ai_block_status_invalid(status):
    with override_settings(BOTS_AI_BLOCK_STATUS=status):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E006"]
    assert isinstance(result[0], Error)


@pytest.mark.parametrize("status", [100, 200, 302, 399])
def test_ai_block_status_not_an_error(status):
    with override_settings(BOTS_AI_BLOCK_STATUS=status):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.W002"]
    assert isinstance(result[0], Warning)


@pytest.mark.parametrize(
    ("name", "hint"),
    [
        ("BOTS_AI_ALLOWED", "Did you mean BOTS_AI_ALLOW?"),
        ("BOTS_CRAWLERS_EXTRA", "Did you mean BOTS_CRAWLER_EXTRA?"),
        ("BOTS_ENABLED", "Remove it."),
    ],
)
def test_unknown_setting_warns(name, hint):
    with override_settings(**{name: ["GPTBot"]}):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.W003"]
    assert isinstance(result[0], Warning)
    assert result[0].hint == hint


def test_ai_allow_unknown_name_warns():
    with override_settings(BOTS_AI_ALLOW=["GPTBot", "GPT-Bot"]):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.W004"]
    assert isinstance(result[0], Warning)
    assert "'GPT-Bot'" in result[0].msg


def test_ai_allow_ignores_invalid_extra():
    with override_settings(BOTS_AI_ALLOW=["NewBot"], BOTS_AI_EXTRA="NewBot"):
        result = run_checks()

    assert {message.id for message in result} == {
        "django_bots.E003",
        "django_bots.W004",
    }


def test_crawler_ignore_unknown_pattern_warns():
    with override_settings(BOTS_CRAWLER_IGNORE=["UptimeRobot", "curl"]):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.W005"]
    assert isinstance(result[0], Warning)
    assert "'curl'" in result[0].msg


def test_ai_block_categories_unknown():
    with override_settings(BOTS_AI_BLOCK_CATEGORIES=["training", "agents"]):
        result = run_checks()

    assert [message.id for message in result] == ["django_bots.E007"]
    assert isinstance(result[0], Error)
    assert "'agents'" in result[0].msg
