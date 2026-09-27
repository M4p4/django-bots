from __future__ import annotations

import pytest
from django.test import RequestFactory

from django_bots.useragent import UserAgent, parse
from django_bots.utils import get_and_set_user_agent, get_user_agent

IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 "
    "(KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3"
)


def test_get_user_agent_parses_header(rf: RequestFactory):
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)

    result = get_user_agent(request)

    assert isinstance(result, UserAgent)
    assert result.ua_string == IPHONE


def test_get_user_agent_without_header(rf: RequestFactory):
    request = rf.get("/")

    result = get_user_agent(request)

    assert isinstance(result, UserAgent)
    assert str(result) == "Other / Other / Other"


def test_get_user_agent_without_meta():
    result = get_user_agent(object())

    assert result == ""


def test_get_and_set_user_agent_sets_attribute(rf: RequestFactory):
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)

    result = get_and_set_user_agent(request)

    assert request.user_agent is result
    assert result.device.family == "iPhone"


def test_get_and_set_user_agent_reuses_attribute(rf: RequestFactory):
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)
    existing = parse("curl/8.7.1")
    request.user_agent = existing  # type: ignore[attr-defined]

    result = get_and_set_user_agent(request)

    assert result is existing


@pytest.mark.parametrize("request_value", [None, ""])
def test_get_and_set_user_agent_without_request(request_value):
    result = get_and_set_user_agent(request_value)

    assert isinstance(result, UserAgent)
    assert result.ua_string == ""
