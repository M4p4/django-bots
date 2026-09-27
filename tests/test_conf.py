from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.apps import apps
from django.test import override_settings

import django_bots
from django_bots.apps import DjangoBotsConfig
from django_bots.conf import bots_settings

DEFAULTS = [
    ("UA_CACHE_SIZE", 2048),
    ("CRAWLER_EXTRA", ()),
    ("CRAWLER_IGNORE", ()),
    ("AI_ALLOW", ()),
    ("AI_EXTRA", ()),
    ("AI_BLOCK_STATUS", 403),
    ("AI_BLOCK_VIEW", None),
    ("AI_BLOCK_EXEMPT_PATHS", ("/robots.txt",)),
]

OVERRIDES = [
    ("UA_CACHE_SIZE", 16),
    ("CRAWLER_EXTRA", ["my-monitor"]),
    ("CRAWLER_IGNORE", ["UptimeRobot"]),
    ("AI_ALLOW", ["OAI-SearchBot"]),
    ("AI_EXTRA", ["NewBot"]),
    ("AI_BLOCK_STATUS", 404),
    ("AI_BLOCK_VIEW", "myapp.views.blocked"),
    ("AI_BLOCK_EXEMPT_PATHS", ["/robots.txt", "/health/"]),
]


def test_every_setting_is_tested():
    names = {name for name in vars(type(bots_settings)) if name.isupper()}

    assert names == {name for name, _ in DEFAULTS} == {name for name, _ in OVERRIDES}


@pytest.mark.parametrize(("name", "expected"), DEFAULTS)
def test_default(name, expected):
    value = getattr(bots_settings, name)

    assert value == expected


@pytest.mark.parametrize(("name", "value"), OVERRIDES)
def test_override(name, value):
    with override_settings(**{f"BOTS_{name}": value}):
        result = getattr(bots_settings, name)

    assert result == value


def test_app_config():
    config = apps.get_app_config("django_bots")

    assert isinstance(config, DjangoBotsConfig)
    assert config.verbose_name == "Bots"


def test_version_matches_pyproject():
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    match = re.search(r'^version = "([^"]+)"$', pyproject.read_text("utf-8"), re.M)

    assert match is not None
    assert django_bots.__version__ == match.group(1)
