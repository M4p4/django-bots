"""Record an ai.robots.txt data update in the version and changelog.

Usage::

    python scripts/bump_version.py v1.53 --before /tmp/ai-robots-before.json

Run it after ``download_ai_robots.py``. When the current version is a release
(``X.Y.Z``) and ``## Unreleased`` has no entries, it bumps the patch version in
``pyproject.toml`` and adds a dated changelog section. Otherwise other changes are
waiting to be released, so it only adds the entry under ``## Unreleased`` and leaves
the version alone. Emits ``release`` (the new version, or empty) like
``check_upstream_version.py``.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from ai_bot_diff import AI_ROBOTS, bot_names, changes
from check_upstream_version import emit

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_LINE = re.compile(r'^version = "([^"]*)"$', re.MULTILINE)
RELEASE = re.compile(r"\A([0-9]+)\.([0-9]+)\.([0-9]+)\Z")
HEADING = "# Changelog\n"
UNRELEASED = "## Unreleased\n"


def read_version(path: Path) -> str:
    matches = VERSION_LINE.findall(path.read_text("utf-8"))
    if len(matches) != 1:
        sys.exit(f"Found {len(matches)} version lines in {path}, expected exactly 1")
    version: str = matches[0]
    return version


def set_version(path: Path, version: str) -> None:
    text = path.read_text("utf-8")
    path.write_text(VERSION_LINE.sub(f'version = "{version}"', text), "utf-8")


def next_patch(version: str) -> str | None:
    """Return the next patch release, or ``None`` if ``version`` isn't ``X.Y.Z``."""
    match = RELEASE.match(version)
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def _split(text: str) -> tuple[bool, str]:
    """Return whether the changelog has an Unreleased heading, and what follows it."""
    if not text.startswith(HEADING):
        sys.exit(f"The changelog does not start with {HEADING!r}")
    body = text[len(HEADING) :].lstrip("\n")
    if body.startswith(UNRELEASED):
        return True, body[len(UNRELEASED) :].lstrip("\n")
    return False, body


def has_unreleased_entries(text: str) -> bool:
    has_heading, rest = _split(text)
    return has_heading and rest.startswith("- ")


def add_unreleased_entry(text: str, entry: str) -> str:
    _, rest = _split(text)
    if rest and not rest.startswith("- "):
        rest = "\n" + rest
    return f"{HEADING}\n{UNRELEASED}\n- {entry}\n{rest}"


def add_release(text: str, version: str, entry: str, today: date) -> str:
    if f"\n## {version} " in text:
        sys.exit(f"The changelog already has an entry for {version}")
    has_heading, rest = _split(text)
    unreleased = f"{UNRELEASED}\n" if has_heading else ""
    section = f"## {version} ({today.isoformat()})\n\n- {entry}\n"
    return f"{HEADING}\n{unreleased}{section}" + (f"\n{rest}" if rest else "")


def entry_text(tag: str, added: int, removed: int) -> str:
    return (
        f"Updated the AI bot list to ai.robots.txt {tag}: "
        f"{added} added, {removed} removed."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="ai.robots.txt release tag, e.g. v1.53")
    parser.add_argument(
        "--before",
        type=Path,
        required=True,
        help="ai_robots.json before the update",
    )
    parser.add_argument("--after", type=Path, default=AI_ROBOTS)
    parser.add_argument("--pyproject", type=Path, default=PYPROJECT)
    parser.add_argument("--changelog", type=Path, default=CHANGELOG)
    args = parser.parse_args()

    added, removed = changes(bot_names(args.before), bot_names(args.after))
    entry = entry_text(args.tag, len(added), len(removed))
    text = args.changelog.read_text("utf-8")
    release = next_patch(read_version(args.pyproject))

    if release is None or has_unreleased_entries(text):
        args.changelog.write_text(add_unreleased_entry(text, entry), "utf-8")
        print(f"Added to Unreleased: {entry}")
        emit(release="")
        return

    set_version(args.pyproject, release)
    args.changelog.write_text(add_release(text, release, entry, date.today()), "utf-8")
    print(f"Bumped to {release}: {entry}")
    emit(release=release)


if __name__ == "__main__":
    main()
