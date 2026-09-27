from __future__ import annotations

import pytest
from django.test import override_settings

import django_bots
from django_bots import ai
from django_bots.ai import ai_bot_names, ai_bots, is_ai_bot, match_ai_bot
from django_bots.useragent import parse

GPTBOT = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; "
    "+https://openai.com/gptbot)"
)
CLAUDEBOT = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; "
    "+claudebot@anthropic.com)"
)
OAI_SEARCHBOT = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; "
    "+https://openai.com/searchbot"
)
BYTESPIDER = (
    "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)"
)
META = "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
WINDOWS_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)
# "spider" in the URL and "openai" in the email match entries when links aren't removed.
BAIDUSPIDER = "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"
CONTACT_ONLY = "Mozilla/5.0 (compatible; Fetcher/1.0; +mailto:crawler@openai.com)"
NEWBOT = "Mozilla/5.0 (compatible; NewBot/1.0)"


@pytest.fixture(autouse=True)
def fresh_matcher():
    ai._get_matcher.cache_clear()
    yield
    ai._get_matcher.cache_clear()


def test_vendored_data():
    bots = ai_bots()

    assert len(bots) > 100
    assert {"GPTBot", "ClaudeBot", "Bytespider", "Google-Extended"} <= set(bots)
    assert {"operator", "respect", "function", "description"} <= set(bots["GPTBot"])


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        (GPTBOT, "GPTBot"),
        (CLAUDEBOT, "ClaudeBot"),
        (OAI_SEARCHBOT, "OAI-SearchBot"),
        (BYTESPIDER, "Bytespider"),
        (GPTBOT.lower(), "GPTBot"),
    ],
)
def test_match(ua_string, expected):
    assert match_ai_bot(ua_string) == expected
    assert is_ai_bot(ua_string) is True


@pytest.mark.parametrize(
    "ua_string",
    [GOOGLEBOT, WINDOWS_CHROME, IPHONE, "", "xGPTBot", BAIDUSPIDER, CONTACT_ONLY],
)
def test_no_match(ua_string):
    assert match_ai_bot(ua_string) is None
    assert is_ai_bot(ua_string) is False


def test_duplicate_spellings_report_the_first():
    first = next(name for name in ai_bots() if name.lower() == "meta-externalagent")

    assert match_ai_bot(META) == first


def test_robots_only_tokens_are_listed():
    assert {"Google-Extended", "Applebot-Extended"} <= set(ai_bot_names())


@pytest.mark.parametrize(
    ("ua_string", "allowed"),
    [(GPTBOT, "gptbot"), (OAI_SEARCHBOT, "OAI-SearchBot")],
)
def test_allow_setting(ua_string, allowed):
    with override_settings(BOTS_AI_ALLOW=[allowed]):
        result = match_ai_bot(ua_string)
        names = ai_bot_names()

    assert result is None
    assert allowed not in names
    assert match_ai_bot(ua_string) is not None


def test_allow_setting_keeps_other_bots():
    with override_settings(BOTS_AI_ALLOW=["OAI-SearchBot"]):
        result = match_ai_bot(CLAUDEBOT)

    assert result == "ClaudeBot"


def test_extra_setting():
    with override_settings(BOTS_AI_EXTRA=["NewBot", "GPTBot"]):
        result = match_ai_bot(NEWBOT)
        names = ai_bot_names()

    assert result == "NewBot"
    assert names[-1] == "NewBot"
    assert names.count("GPTBot") == 1
    assert match_ai_bot(NEWBOT) is None


def test_no_names_matches_nothing():
    with override_settings(BOTS_AI_ALLOW=list(ai_bots())):
        result = match_ai_bot(GPTBOT)

    assert result is None


def test_results_are_cached():
    match_ai_bot(GPTBOT)
    match_ai_bot(GPTBOT)

    matcher = ai._get_matcher(2048, (), ())

    assert matcher.cache_info().hits == 1  # type: ignore[attr-defined]


def test_zero_cache_size_disables_cache():
    with override_settings(BOTS_UA_CACHE_SIZE=0):
        result = match_ai_bot(GPTBOT)
        matcher = ai._get_matcher(0, (), ())

    assert result == "GPTBot"
    assert not hasattr(matcher, "cache_info")


@pytest.mark.parametrize(
    ("ua_string", "ai_bot", "is_bot"),
    [
        (GPTBOT, "GPTBot", True),
        (BYTESPIDER, "Bytespider", True),
        (GOOGLEBOT, None, True),
        (WINDOWS_CHROME, None, False),
    ],
)
def test_user_agent_attributes(ua_string, ai_bot, is_bot):
    result = parse(ua_string)

    assert result.ai_bot == ai_bot
    assert result.is_ai_bot is (ai_bot is not None)
    assert result.is_bot is is_bot


def test_crawler_is_bot():
    result = parse("python-requests/2.32.3")

    assert result.device.family != "Spider"
    assert result.is_bot is True


def test_data_versions():
    versions = django_bots.DATA_VERSIONS

    assert set(versions) == {
        "ai_robots_txt",
        "crawler_user_agents",
        "ua_parser",
        "uap_core",
    }
    assert versions["ai_robots_txt"].startswith("v")
