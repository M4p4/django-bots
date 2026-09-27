"""Accepted differences from user-agents 2.2.0 in the compat test.

Maps a user-agent string from ``tests/data/user_agents.txt`` to the attribute
names that may differ, each with a comment giving the reason. Keep this short.
"""

from __future__ import annotations

COMPAT_EXCEPTIONS: dict[str, frozenset[str]] = {}
