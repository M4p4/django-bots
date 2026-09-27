"""Parse user-agent strings into browser, OS and device details.

The API matches ``user_agents.parsers`` from the `user-agents
<https://github.com/selwin/python-user-agents>`_ package, so code written for
django-user-agents keeps working. The ``is_mobile``, ``is_tablet``, ``is_pc``,
``is_touch_capable`` and ``is_email_client`` rules are ported from user-agents
2.2.0, copyright (c) 2013 Selwin Ong, released under the MIT license.

Parsing uses `ua-parser <https://github.com/ua-parser/uap-python>`_ with an
in-process LRU cache of ``BOTS_UA_CACHE_SIZE`` entries.
"""

from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

import ua_parser
from ua_parser import Cache, CachingResolver, Resolver
from ua_parser.caching import Lru

from django_bots.conf import bots_settings

__all__ = ["Browser", "Device", "OperatingSystem", "UserAgent", "parse"]

MOBILE_DEVICE_FAMILIES = frozenset(
    {
        "iPhone",
        "iPod",
        "Generic Smartphone",
        "Generic Feature Phone",
        "PlayStation Vita",
        "iOS-Device",
    }
)

PC_OS_FAMILIES = frozenset({"Windows 95", "Windows 98", "Solaris"})

MOBILE_OS_FAMILIES = frozenset(
    {
        "Windows Phone",
        "Windows Phone OS",
        "Symbian OS",
        "Bada",
        "Windows CE",
        "Windows Mobile",
        "Maemo",
    }
)

MOBILE_BROWSER_FAMILIES = frozenset(
    {
        "IE Mobile",
        "Opera Mobile",
        "Opera Mini",
        "Chrome Mobile",
        "Chrome Mobile WebView",
        "Chrome Mobile iOS",
    }
)

TABLET_DEVICE_FAMILIES = frozenset(
    {
        "iPad",
        "BlackBerry Playbook",
        "Blackberry Playbook",
        "Kindle",
        "Kindle Fire",
        "Kindle Fire HD",
        "Galaxy Tab",
        "Xoom",
        "Dell Streak",
    }
)

TOUCH_CAPABLE_OS_FAMILIES = frozenset(
    {
        "iOS",
        "Android",
        "Windows Phone",
        "Windows CE",
        "Windows Mobile",
        "Firefox OS",
        "MeeGo",
    }
)

TOUCH_CAPABLE_DEVICE_FAMILIES = frozenset(
    {"BlackBerry Playbook", "Blackberry Playbook", "Kindle Fire"}
)

EMAIL_PROGRAM_FAMILIES = frozenset(
    {
        "Outlook",
        "Windows Live Mail",
        "AirMail",
        "Apple Mail",
        "Thunderbird",
        "Lightning",
        "ThunderBrowse",
        "The Bat!",
        "Lotus Notes",
        "IBM Notes",
        "Barca",
        "MailBar",
        "kmail2",
        "YahooMobileMail",
    }
)

Version = tuple[int | str, ...]


class Browser(NamedTuple):
    """The browser family and version."""

    family: str
    version: Version
    version_string: str


class OperatingSystem(NamedTuple):
    """The operating system family and version."""

    family: str
    version: Version
    version_string: str


class Device(NamedTuple):
    """The device family, brand and model."""

    family: str
    brand: str | None
    model: str | None


def _parse_version(*parts: str | None) -> tuple[Version, str]:
    """Turn version parts into a tuple, with digit-only parts as ints."""
    version = tuple(int(p) if p.isdigit() else p for p in parts if p is not None)
    return version, ".".join(str(p) for p in version)


@lru_cache(maxsize=1)
def _get_parser(cache_size: int) -> ua_parser.Parser:
    """Build the parser, with a new cache whenever the cache size changes."""
    if ua_parser.BestAvailableResolver is ua_parser.BasicResolver:
        matchers = ua_parser.load_builtins()
    else:
        matchers = ua_parser.load_lazy_builtins()
    resolver: Resolver = ua_parser.BestAvailableResolver(matchers)
    if cache_size > 0:
        cache: Cache = Lru(cache_size)
        resolver = CachingResolver(resolver, cache)
    return ua_parser.Parser(resolver)


class UserAgent:
    """A parsed user-agent string."""

    def __init__(self, user_agent_string: str) -> None:
        result = (
            _get_parser(bots_settings.UA_CACHE_SIZE)
            .parse(user_agent_string)
            .with_defaults()
        )
        self.ua_string = user_agent_string

        ua = result.user_agent
        version, version_string = _parse_version(ua.major, ua.minor, ua.patch)
        self.browser = Browser(ua.family, version, version_string)

        os = result.os
        version, version_string = _parse_version(os.major, os.minor, os.patch)
        self.os = OperatingSystem(os.family, version, version_string)

        device = result.device
        self.device = Device(device.family, device.brand, device.model)

    def __str__(self) -> str:
        return f"{self.get_device()} / {self.get_os()} / {self.get_browser()}"

    def __repr__(self) -> str:
        return f"<UserAgent {self.ua_string!r}>"

    def _is_android_tablet(self) -> bool:
        # Newer Android tablets leave "Mobile" out of the UA, older ones still send it.
        return (
            "Mobile Safari" not in self.ua_string
            and self.browser.family != "Firefox Mobile"
        )

    def _is_blackberry_touch_capable_device(self) -> bool:
        return (
            "Blackberry 99" in self.device.family
            or "Blackberry 95" in self.device.family
        )

    def get_device(self) -> str:
        """Return ``"PC"`` for desktops, else the device family."""
        return "PC" if self.is_pc else self.device.family

    def get_os(self) -> str:
        """Return the OS family and version, for example ``"iOS 5.1"``."""
        return f"{self.os.family} {self.os.version_string}".strip()

    def get_browser(self) -> str:
        """Return the browser family and version, for example ``"Safari 5.1"``."""
        return f"{self.browser.family} {self.browser.version_string}".strip()

    @property
    def is_tablet(self) -> bool:
        """Whether the device is a tablet."""
        return (
            self.device.family in TABLET_DEVICE_FAMILIES
            or (self.os.family == "Android" and self._is_android_tablet())
            or (self.os.family == "Windows" and self.os.version_string.startswith("RT"))
            or (self.os.family == "Firefox OS" and "Mobile" not in self.browser.family)
        )

    @property
    def is_mobile(self) -> bool:
        """Whether the device is a phone (tablets are not mobile)."""
        ua_string = self.ua_string
        return (
            self.device.family in MOBILE_DEVICE_FAMILIES
            or self.browser.family in MOBILE_BROWSER_FAMILIES
            # Android and Firefox OS devices are phones unless they're tablets.
            or (self.os.family in ("Android", "Firefox OS") and not self.is_tablet)
            or (
                self.os.family == "BlackBerry OS"
                and self.device.family != "Blackberry Playbook"
            )
            or self.os.family in MOBILE_OS_FAMILIES
            or "J2ME" in ua_string
            or "MIDP" in ua_string
            or "iPhone;" in ua_string
            or "Googlebot-Mobile" in ua_string
            or (self.device.family == "Spider" and "Mobile" in self.browser.family)
            or ("NokiaBrowser" in ua_string and "Mobile" in ua_string)
        )

    @property
    def is_touch_capable(self) -> bool:
        """Whether the device has a touch screen."""
        if (
            self.os.family in TOUCH_CAPABLE_OS_FAMILIES
            or self.device.family in TOUCH_CAPABLE_DEVICE_FAMILIES
        ):
            return True
        if self.os.family == "Windows" and (
            self.os.version_string.startswith(("RT", "CE"))
            or (self.os.version_string.startswith("8") and "Touch" in self.ua_string)
        ):
            return True
        return (
            "BlackBerry" in self.os.family
            and self._is_blackberry_touch_capable_device()
        )

    @property
    def is_pc(self) -> bool:
        """Whether the device is a desktop or laptop (Windows, macOS, Linux)."""
        ua_string = self.ua_string
        if (
            "Windows NT" in ua_string
            or self.os.family in PC_OS_FAMILIES
            or (self.os.family == "Windows" and self.os.version_string == "ME")
        ):
            return True
        if self.os.family == "Mac OS X" and "Silk" not in ua_string:
            return True
        # Maemo sends "Linux" and "X11", but it's a phone.
        if "Maemo" in ua_string:
            return False
        return "Chrome OS" in self.os.family or (
            "Linux" in ua_string and "X11" in ua_string
        )

    @property
    def is_bot(self) -> bool:
        """Whether ua-parser classifies the device as a spider."""
        return self.device.family == "Spider"

    @property
    def is_email_client(self) -> bool:
        """Whether the user agent is an email client."""
        return self.browser.family in EMAIL_PROGRAM_FAMILIES


def parse(user_agent_string: str | None) -> UserAgent:
    """Parse a user-agent string. ``None`` parses like an empty string."""
    return UserAgent(user_agent_string or "")
