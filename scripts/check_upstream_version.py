"""Compare the bundled ai.robots.txt release with the latest upstream release.

Usage::

    python scripts/check_upstream_version.py
    python scripts/check_upstream_version.py --upstream v1.53

Prints ``bundled``, ``upstream`` and ``sync`` as ``key=value`` lines, and appends the
same lines to ``$GITHUB_OUTPUT`` when running under Actions. ``sync`` is only ``true``
when upstream is numerically newer, so the data is never downgraded. A tag that isn't
``vX.Y`` (a prerelease, say) reports ``sync=false`` instead of failing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

LATEST_URL = "https://api.github.com/repos/ai-robots-txt/ai.robots.txt/releases/latest"
TIMEOUT = 30
VERSIONS = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "django_bots"
    / "data"
    / "VERSIONS.json"
)
TAG = re.compile(r"\Av?([0-9]+(?:\.[0-9]+)*)\Z")


def bundled_version(path: Path) -> str:
    version: str = json.loads(path.read_text("utf-8"))["ai_robots_txt"]
    return version


def latest_version() -> str:
    request = urllib.request.Request(
        LATEST_URL, headers={"Accept": "application/vnd.github+json"}
    )
    # Authenticated requests avoid the low anonymous rate limit on shared runners.
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310
            tag: str = json.loads(response.read())["tag_name"]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError) as exc:
        sys.exit(f"Failed to read the latest release from {LATEST_URL}: {exc}")
    return tag


def as_tuple(tag: str) -> tuple[int, ...] | None:
    match = TAG.match(tag)
    if match is None:
        return None
    return tuple(int(part) for part in match[1].split("."))


def emit(**outputs: str) -> None:
    for key, value in outputs.items():
        # A newline would let a crafted value add further lines to $GITHUB_OUTPUT.
        if "\n" in value or "\r" in value:
            sys.exit(f"Refusing to emit {key} containing a newline: {value!r}")
        print(f"{key}={value}")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as file:
            for key, value in outputs.items():
                file.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upstream",
        help="Release tag to compare against instead of querying GitHub",
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=VERSIONS,
        help=f"Path to VERSIONS.json (default: {VERSIONS})",
    )
    args = parser.parse_args()

    bundled = bundled_version(args.versions)
    bundled_tuple = as_tuple(bundled)
    if bundled_tuple is None:
        sys.exit(f"Bundled tag {bundled!r} is not a numeric version")

    upstream = args.upstream or latest_version()
    upstream_tuple = as_tuple(upstream)
    if upstream_tuple is None:
        print(f"::notice::ignoring non-numeric upstream tag {upstream!r}")
        emit(bundled=bundled, upstream=upstream, sync="false")
        return

    emit(
        bundled=bundled,
        upstream=upstream,
        sync="true" if upstream_tuple > bundled_tuple else "false",
    )


if __name__ == "__main__":
    main()
