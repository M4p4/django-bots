from __future__ import annotations

import pytest
import ua_parser
from django.test import override_settings
from ua_parser import CachingResolver

from django_bots import useragent
from django_bots.conf import UA_MAX_LENGTH
from django_bots.useragent import Browser, Device, OperatingSystem, UserAgent, parse

IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 "
    "(KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3"
)
WINDOWS_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


@pytest.fixture(autouse=True)
def fresh_parser():
    useragent._get_parser.cache_clear()
    yield
    useragent._get_parser.cache_clear()


def test_parse_iphone():
    result = parse(IPHONE)

    assert result.ua_string == IPHONE
    assert result.browser == Browser("Mobile Safari", (5, 1), "5.1")
    assert result.os == OperatingSystem("iOS", (5, 1), "5.1")
    assert result.device == Device("iPhone", "Apple", "iPhone")
    assert str(result) == "iPhone / iOS 5.1 / Mobile Safari 5.1"
    assert result.get_device() == "iPhone"
    assert result.get_os() == "iOS 5.1"
    assert result.get_browser() == "Mobile Safari 5.1"


def test_parse_desktop_reports_pc_device():
    result = parse(WINDOWS_CHROME)

    assert result.get_device() == "PC"
    assert result.get_os() == "Windows 10"
    assert result.get_browser() == "Chrome 126.0.0"


def test_version_keeps_non_numeric_parts():
    result = parse(
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; ARM; Trident/6.0; Touch)"
    )

    assert result.os == OperatingSystem("Windows", ("RT",), "RT")


@pytest.mark.parametrize("ua_string", ["", None])
def test_parse_empty_or_missing(ua_string):
    result = parse(ua_string)

    assert result.ua_string == ""
    assert result.browser == Browser("Other", (), "")
    assert result.os == OperatingSystem("Other", (), "")
    assert result.device == Device("Other", None, None)
    assert str(result) == "Other / Other / Other"


@pytest.mark.parametrize(
    ("ua_string", "is_bot"),
    [(GOOGLEBOT, True), (IPHONE, False), (WINDOWS_CHROME, False)],
)
def test_is_bot(ua_string, is_bot):
    result = parse(ua_string)

    assert result.is_bot is is_bot


def test_long_user_agent_parses_the_start():
    ua_string = WINDOWS_CHROME + " " + "x" * UA_MAX_LENGTH + " iPhone"

    result = parse(ua_string)

    assert result.ua_string == ua_string
    assert result.browser.family == "Chrome"
    assert result.os.family == "Windows"


def test_user_agent_constructor_parses():
    result = UserAgent(IPHONE)

    assert result.device.family == "iPhone"


def test_repr():
    result = parse("curl/8.7.1")

    assert repr(result) == "<UserAgent 'curl/8.7.1'>"


def test_parser_uses_cache_size_setting():
    with override_settings(BOTS_UA_CACHE_SIZE=16):
        parse(IPHONE)
        resolver = useragent._get_parser(16).resolver

    assert isinstance(resolver, CachingResolver)
    assert resolver.cache.maxsize == 16


def test_zero_cache_size_disables_cache():
    with override_settings(BOTS_UA_CACHE_SIZE=0):
        result = parse(IPHONE)
        resolver = useragent._get_parser(0).resolver

    assert result.device.family == "iPhone"
    assert not isinstance(resolver, CachingResolver)


@pytest.mark.parametrize(
    ("backend", "loader"),
    [
        (ua_parser.BasicResolver, "load_builtins"),
        (lambda matchers: ua_parser.BasicResolver(matchers), "load_lazy_builtins"),
    ],
)
def test_matchers_fit_backend(monkeypatch, backend, loader):
    calls = []
    real_loader = getattr(ua_parser, loader)

    def spy():
        calls.append(loader)
        return real_loader()

    monkeypatch.setattr(ua_parser, "BestAvailableResolver", backend)
    monkeypatch.setattr(ua_parser, loader, spy)

    result = parse(IPHONE)

    assert calls == [loader]
    assert result.device.family == "iPhone"
