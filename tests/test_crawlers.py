from __future__ import annotations

import pytest
from django.test import override_settings

from django_bots import crawlers
from django_bots.conf import UA_MAX_LENGTH
from django_bots.crawlers import crawler_patterns, is_crawler
from django_bots.useragent import parse

GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BINGBOT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
PYTHON_REQUESTS = "python-requests/2.32.3"
UPTIMEROBOT = "Mozilla/5.0+(compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)"
WINDOWS_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
MY_MONITOR = "my-monitor/1.0"

HUMANS = [
    WINDOWS_CHROME,
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
    ),
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:127.0) Gecko/20100101 Firefox/127.0",
    (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
    ),
    (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
    ),
    "",
]


@pytest.fixture(autouse=True)
def fresh_matcher():
    crawlers._get_matcher.cache_clear()
    yield
    crawlers._get_matcher.cache_clear()


@pytest.mark.parametrize(
    "ua_string",
    [GOOGLEBOT, BINGBOT, PYTHON_REQUESTS, UPTIMEROBOT, PYTHON_REQUESTS.upper()],
)
def test_crawler(ua_string):
    assert is_crawler(ua_string) is True


@pytest.mark.parametrize("ua_string", HUMANS)
def test_human(ua_string):
    assert is_crawler(ua_string) is False


@pytest.mark.parametrize(("padding", "expected"), [(0, True), (UA_MAX_LENGTH, False)])
def test_only_the_start_is_matched(padding, expected):
    ua_string = "x" * padding + " " + GOOGLEBOT

    assert is_crawler(ua_string) is expected


def test_extra_setting():
    with override_settings(BOTS_CRAWLER_EXTRA=["^my-monitor/"]):
        result = is_crawler(MY_MONITOR)

    assert result is True
    assert is_crawler(MY_MONITOR) is False


def test_ignore_setting():
    with override_settings(BOTS_CRAWLER_IGNORE=["UptimeRobot"]):
        result = is_crawler(UPTIMEROBOT)

    assert result is False
    assert is_crawler(UPTIMEROBOT) is True


def test_crawler_patterns_applies_settings():
    with override_settings(
        BOTS_CRAWLER_EXTRA=["^my-monitor/"], BOTS_CRAWLER_IGNORE=["UptimeRobot"]
    ):
        result = crawler_patterns()

    assert "UptimeRobot" not in result
    assert result[-1] == "^my-monitor/"
    assert "Googlebot\\/" in result


def test_no_patterns_matches_nothing():
    with override_settings(BOTS_CRAWLER_IGNORE=crawler_patterns()):
        result = is_crawler(GOOGLEBOT)

    assert result is False


def test_results_are_cached():
    is_crawler(GOOGLEBOT)
    is_crawler(GOOGLEBOT)

    matcher = crawlers._get_matcher(2048, (), ())

    assert matcher.cache_info().hits == 1  # type: ignore[attr-defined]


def test_cache_size_setting():
    with override_settings(BOTS_UA_CACHE_SIZE=16):
        is_crawler(GOOGLEBOT)
        matcher = crawlers._get_matcher(16, (), ())

    assert matcher.cache_info().maxsize == 16  # type: ignore[attr-defined]


def test_zero_cache_size_disables_cache():
    with override_settings(BOTS_UA_CACHE_SIZE=0):
        result = is_crawler(GOOGLEBOT)
        matcher = crawlers._get_matcher(0, (), ())

    assert result is True
    assert not hasattr(matcher, "cache_info")


@pytest.mark.parametrize(
    ("ua_string", "expected"), [(GOOGLEBOT, True), (WINDOWS_CHROME, False)]
)
def test_user_agent_is_crawler(ua_string, expected):
    result = parse(ua_string)

    assert result.is_crawler is expected
