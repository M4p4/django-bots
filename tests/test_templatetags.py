from __future__ import annotations

import pytest
from django.template import Context, Template

IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 "
    "(KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3"
)
IPAD = (
    "Mozilla/5.0 (iPad; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 "
    "(KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10"
)
WINDOWS_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
GPTBOT = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; "
    "+https://openai.com/gptbot)"
)

TEMPLATE = (
    "{% load user_agents %}"
    "{{ request|is_mobile }} {{ request|is_tablet }} {{ request|is_touch_capable }} "
    "{{ request|is_pc }} {{ request|is_bot }}"
)


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        (IPHONE, "True False True False False"),
        (IPAD, "False True True False False"),
        (WINDOWS_CHROME, "False False False True False"),
        (GOOGLEBOT, "False False False False True"),
    ],
)
def test_filters(rf, ua_string, expected):
    request = rf.get("/", HTTP_USER_AGENT=ua_string)

    result = Template(TEMPLATE).render(Context({"request": request}))

    assert result == expected


def test_filters_set_user_agent_once(rf):
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)

    Template(TEMPLATE).render(Context({"request": request}))

    assert request.user_agent.ua_string == IPHONE


def test_filters_without_request():
    result = Template(TEMPLATE).render(Context())

    assert result == "False False False False False"


BOTS_TEMPLATE = (
    "{% load bots %}"
    "{{ request|is_ai_bot }} {{ request|is_crawler }} {{ request|is_mobile }} {{ request|is_tablet }} "
    "{{ request|is_touch_capable }} {{ request|is_pc }} {{ request|is_bot }}"
)


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        (IPHONE, "False False True False True False False"),
        (WINDOWS_CHROME, "False False False False False True False"),
        (GOOGLEBOT, "False True False False False False True"),
        (GPTBOT, "True True False False False False True"),
    ],
)
def test_bots_filters(rf, ua_string, expected):
    request = rf.get("/", HTTP_USER_AGENT=ua_string)

    result = Template(BOTS_TEMPLATE).render(Context({"request": request}))

    assert result == expected


def test_bots_filters_without_request():
    result = Template(BOTS_TEMPLATE).render(Context())

    assert result == "False False False False False False False"
