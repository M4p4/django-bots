from __future__ import annotations

import time

import pytest
from django.test import override_settings

import django_bots
from django_bots import ai
from django_bots.ai import (
    AI_BOT_CATEGORIES,
    URL_OR_EMAIL,
    ai_bot_category,
    ai_bot_names,
    ai_bots,
    categorize,
    is_ai_bot,
    match_ai_bot,
    match_ai_bots,
    robots_rules,
)
from django_bots.conf import UA_MAX_LENGTH
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
BARE_URL = "MyCrawler/1.0 (+openai.com/gptbot)"
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
    [
        GOOGLEBOT,
        WINDOWS_CHROME,
        IPHONE,
        "",
        "xGPTBot",
        BAIDUSPIDER,
        CONTACT_ONLY,
        BARE_URL,
    ],
)
def test_no_match(ua_string):
    assert match_ai_bot(ua_string) is None
    assert is_ai_bot(ua_string) is False


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        ("Fetcher/1.0 (+crawler@openai.com)", "Fetcher/1.0 ( )"),
        ("Fetcher/1.0 (a.b+c@openai.com)", "Fetcher/1.0 ( )"),
        ("Fetcher/1.0 (+https://openai.com/bot)", "Fetcher/1.0 (+ )"),
        ("Fetcher/1.0 (+openai.com/bot)", "Fetcher/1.0 (+ )"),
        ("Fetcher/1.0 (+docs.openai.com/bots/; x)", "Fetcher/1.0 (+ ; x)"),
        ("GPTBot/1.2 (openai.com)", "GPTBot/1.2 (openai.com)"),
    ],
)
def test_links_are_removed(ua_string, expected):
    assert URL_OR_EMAIL.sub(" ", ua_string) == expected


@pytest.mark.parametrize("ua_string", ["a" * 20_000, "a." * 10_000, "a-" * 10_000])
def test_link_removal_is_linear(ua_string):
    start = time.perf_counter()

    URL_OR_EMAIL.sub(" ", ua_string)

    assert time.perf_counter() - start < 0.1


@pytest.mark.parametrize(
    ("padding", "expected"), [(0, "GPTBot"), (UA_MAX_LENGTH, None)]
)
def test_only_the_start_is_matched(padding, expected):
    ua_string = "x" * padding + " GPTBot/1.2"

    assert match_ai_bot(ua_string) == expected


def test_duplicate_spellings_report_the_first():
    first = next(name for name in ai_bots() if name.lower() == "meta-externalagent")

    assert match_ai_bot(META) == first


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        ("MistralAI-User/1.0", "MistralAI-User"),
        ("Mozilla/5.0 (compatible; MistralAI-User/1.1)", "MistralAI-User"),
        ("iaskspider/2.0", "iaskspider"),
        ("iaskspider/2.1", "iaskspider"),
        ("Brightbot 1.0", "Brightbot"),
        ("Brightbot 2.0", "Brightbot"),
    ],
)
def test_versioned_spellings_report_the_base_name(ua_string, expected):
    assert match_ai_bot(ua_string) == expected


def test_versioned_spelling_without_base_name():
    with override_settings(BOTS_AI_EXTRA=["NewBot/2.0"]):
        result = match_ai_bot("NewBot/2.0")

    assert result == "NewBot/2.0"


def test_versioned_extra_reports_the_base_name():
    with override_settings(BOTS_AI_EXTRA=["NewBot", "NewBot v2"]):
        result = match_ai_bot("NewBot v2")

    assert result == "NewBot"


def test_allow_setting_covers_versioned_spellings():
    with override_settings(BOTS_AI_ALLOW=["mistralai-user"]):
        result = match_ai_bot("MistralAI-User/1.0")
        names = ai_bot_names()

    assert result is None
    assert "MistralAI-User/1.0" not in names


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


def test_robots_rules_format(monkeypatch):
    monkeypatch.setattr(ai, "ai_bots", lambda: {"GPTBot": {}, "ChatGPT Agent": {}})

    with override_settings(BOTS_AI_EXTRA=["NewBot"]):
        result = robots_rules()

    assert result == (
        "User-agent: GPTBot\nUser-agent: ChatGPT Agent\nUser-agent: NewBot\nDisallow: /"
    )


def test_robots_rules_keep_duplicate_spellings():
    result = robots_rules()

    assert "User-agent: meta-externalagent\n" in result
    assert "User-agent: Meta-ExternalAgent\n" in result
    assert "User-agent: Google-Extended\n" in result
    assert "User-agent: MistralAI-User/1.0\n" in result


def test_robots_rules_allow_setting():
    with override_settings(BOTS_AI_ALLOW=["gptbot"]):
        result = robots_rules()

    assert "GPTBot" not in result
    assert "User-agent: ClaudeBot\n" in result


def test_robots_rules_without_names():
    with override_settings(BOTS_AI_ALLOW=list(ai_bots())):
        result = robots_rules()

    assert result == ""


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


def test_every_bundled_name_has_a_category():
    categories = {categorize(name, entry) for name, entry in ai_bots().items()}

    assert categories == set(AI_BOT_CATEGORIES)


def test_category_overrides_are_valid():
    groups = ai._read_data("ai_categories.json")
    names = [name for group in groups.values() for name in group]

    assert set(groups) <= set(AI_BOT_CATEGORIES)
    assert len(names) == len(set(names))
    assert set(names) <= set(ai_bots())


@pytest.mark.parametrize(
    ("name", "entry", "expected"),
    [
        ("NewBot", {"function": "AI Coding Agents"}, "agent"),
        ("NewBot", {"function": "AI Search Crawlers"}, "search"),
        ("NewBot", {"function": "AI Assistants"}, "assistant"),
        ("NewBot", {"function": "LLM training."}, "training"),
        ("NewBot", {}, "training"),
        ("PerplexityBot", {"function": "Search result generation."}, "search"),
        ("NewBot", {"function": "Undocumented AI Agents"}, "training"),
    ],
)
def test_categorize(name, entry, expected):
    assert categorize(name, entry) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("GPTBot", "training"),
        ("gptbot", "training"),
        ("OAI-SearchBot", "search"),
        ("ChatGPT-User", "assistant"),
        ("MistralAI-User", "assistant"),
        ("Cursor", "agent"),
        ("Code", "agent"),
        ("Googlebot", None),
    ],
)
def test_ai_bot_category(name, expected):
    assert ai_bot_category(name) == expected


def test_extra_names_are_training():
    with override_settings(BOTS_AI_EXTRA=["NewBot"]):
        result = ai_bot_category("newbot")

    assert result == "training"


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        (GPTBOT, "training"),
        (OAI_SEARCHBOT, "search"),
        (
            "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Code/1.104.0 Chrome/138.0.7204.100 Electron/37.3.1 Safari/537.36",
            "agent",
        ),
        (WINDOWS_CHROME, None),
    ],
)
def test_user_agent_category(ua_string, expected):
    assert parse(ua_string).ai_bot_category == expected


@pytest.mark.parametrize(
    ("ua_string", "expected"),
    [
        ("Operator/1.0 ClaudeBot/1.0", ("Operator", "ClaudeBot")),
        ("GPTBot/1.2 gptbot GPTBot", ("GPTBot",)),
        (GPTBOT, ("GPTBot",)),
        (WINDOWS_CHROME, ()),
    ],
)
def test_match_all_names(ua_string, expected):
    assert match_ai_bots(ua_string) == expected
    assert match_ai_bot(ua_string) == (expected[0] if expected else None)
