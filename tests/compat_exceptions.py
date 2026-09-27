"""Accepted differences from user-agents 2.2.0 in the compat test.

Maps a user-agent string from ``tests/data/user_agents.txt`` to the attribute
names that may differ, each with a comment giving the reason. Keep this short.
"""

from __future__ import annotations

# Firefox on Android and Firefox OS tablets: ua-parser reports "Generic Tablet".
_FIREFOX_TABLET = frozenset({"is_mobile", "is_tablet"})

COMPAT_EXCEPTIONS: dict[str, frozenset[str]] = {
    "Mozilla/5.0 (Android 13; Tablet; rv:126.0) Gecko/126.0 Firefox/126.0": _FIREFOX_TABLET,
    "Mozilla/5.0 (Android 4.4; Tablet; rv:41.0) Gecko/41.0 Firefox/41.0": _FIREFOX_TABLET,
    "Mozilla/5.0 (Tablet; rv:26.0) Gecko/26.0 Firefox/26.0": _FIREFOX_TABLET,
}
