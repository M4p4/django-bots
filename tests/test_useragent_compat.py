"""Compare the parser with user-agents 2.2.0 on real user-agent strings."""

from __future__ import annotations

from pathlib import Path

import pytest
import user_agents

from django_bots.useragent import parse
from tests.compat_exceptions import COMPAT_EXCEPTIONS

ATTRIBUTES = (
    "ua_string",
    "browser",
    "os",
    "device",
    "is_mobile",
    "is_tablet",
    "is_pc",
    "is_touch_capable",
    "is_email_client",
)

UA_STRINGS = [
    line
    for line in (Path(__file__).parent / "data" / "user_agents.txt")
    .read_text()
    .splitlines()
    if line and not line.startswith("#")
]


def _attributes(user_agent: object, skip: frozenset[str]) -> dict[str, object]:
    values = {
        name: getattr(user_agent, name) for name in ATTRIBUTES if name not in skip
    }
    values["str"] = str(user_agent)
    return values


def test_fixture_has_no_duplicates():
    assert len(UA_STRINGS) == len(set(UA_STRINGS))


def test_exceptions_refer_to_fixture_strings():
    assert set(COMPAT_EXCEPTIONS) <= set(UA_STRINGS)


@pytest.mark.parametrize("ua_string", UA_STRINGS)
def test_matches_user_agents(ua_string):
    skip = COMPAT_EXCEPTIONS.get(ua_string, frozenset())

    result = _attributes(parse(ua_string), skip)

    assert result == _attributes(user_agents.parse(ua_string), skip)


@pytest.mark.parametrize("ua_string", UA_STRINGS)
def test_is_bot_covers_user_agents(ua_string):
    # is_bot also includes crawlers and AI bots, so it only has to agree when the old one is true.
    result = parse(ua_string).is_bot

    assert result or not user_agents.parse(ua_string).is_bot
