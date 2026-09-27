"""Summarize which AI bots an ai.robots.txt update adds and removes.

Usage::

    cp src/django_bots/data/ai_robots.json /tmp/ai-robots-before.json
    python scripts/download_ai_robots.py v1.53
    python scripts/ai_bot_diff.py /tmp/ai-robots-before.json

Writes a Markdown summary for the pull request body. The data file diff is long and
mostly descriptions; the added and removed names are what changes behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from django_bots.ai import categorize

AI_ROBOTS = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "django_bots"
    / "data"
    / "ai_robots.json"
)


def bot_names(path: Path) -> set[str]:
    return set(read_bots(path))


def read_bots(path: Path) -> dict[str, dict[str, Any]]:
    bots: dict[str, dict[str, Any]] = json.loads(path.read_text("utf-8"))
    return bots


def changes(before: set[str], after: set[str]) -> tuple[list[str], list[str]]:
    """Return the added and removed names, each sorted case-insensitively."""
    return (
        sorted(after - before, key=str.lower),
        sorted(before - after, key=str.lower),
    )


def _listing(heading: str, names: list[str]) -> list[str]:
    if not names:
        return []
    return [f"### {heading} ({len(names)})", "", ", ".join(names), ""]


def summarize(before: set[str], after: dict[str, dict[str, Any]]) -> str:
    """Summarize the change, with the category each added name gets."""
    added, removed = changes(before, set(after))
    lines = [f"{len(before)} AI bots before, {len(after)} after.", ""]
    if removed:
        lines += [
            "Removed names are no longer blocked or listed in robots.txt output.",
            "",
        ]
    if added:
        lines += [
            "Check the category of each added name. Only `agent` isn't blocked by default;",
            "correct one in `src/django_bots/data/ai_categories.json`.",
            "",
        ]
    lines += _listing("Added", [f"`{n}` ({categorize(n, after[n])})" for n in added])
    lines += _listing("Removed", [f"`{n}`" for n in removed])
    if not added and not removed:
        lines.append("No names added or removed; only entry details changed.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="ai_robots.json before the update")
    parser.add_argument(
        "--after",
        type=Path,
        default=AI_ROBOTS,
        help=f"ai_robots.json after the update (default: {AI_ROBOTS})",
    )
    args = parser.parse_args()

    print(summarize(bot_names(args.before), read_bots(args.after)), end="")


if __name__ == "__main__":
    main()
