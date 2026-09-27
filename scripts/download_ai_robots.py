"""Vendor the AI bot list from an ai.robots.txt release.

Usage::

    python scripts/download_ai_robots.py v1.52

Writes ``robots.json`` from that release tag to ``src/django_bots/data/ai_robots.json``,
records the tag in ``data/VERSIONS.json`` and copies the upstream license to
``data/LICENSE-ai-robots-txt``. Output is deterministic: re-running for the same tag
produces byte-identical files.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RAW_URL = "https://raw.githubusercontent.com/ai-robots-txt/ai.robots.txt/{tag}/{path}"
TIMEOUT = 60
DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "django_bots" / "data"


def download(tag: str, path: str) -> bytes:
    url = RAW_URL.format(tag=tag, path=path)
    print(f"Downloading {url}")
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:  # noqa: S310
            data: bytes = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f"Failed to download {url}: {exc}")
    return data


def normalize(raw: bytes) -> dict[str, dict[str, Any]]:
    """Parse ``robots.json`` and check that every entry is a name mapped to an object."""
    data = json.loads(raw)
    if not isinstance(data, dict) or not data:
        sys.exit("robots.json is not a non-empty object")
    invalid = sorted(
        name
        for name, entry in data.items()
        if not name.strip() or not isinstance(entry, dict)
    )
    if invalid:
        sys.exit(f"Invalid robots.json entries: {', '.join(invalid[:5])}")
    return {name: data[name] for name in sorted(data, key=str.lower)}


def write_json(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_data(
    tag: str, bots: dict[str, dict[str, Any]], license_text: bytes, data_dir: Path
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    write_json(data_dir / "ai_robots.json", bots)
    write_json(data_dir / "VERSIONS.json", {"ai_robots_txt": tag})
    (data_dir / "LICENSE-ai-robots-txt").write_bytes(license_text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="ai.robots.txt release tag to vendor, e.g. v1.52")
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR,
        help=f"Directory to write the data to (default: {DATA_DIR})",
    )
    args = parser.parse_args()

    bots = normalize(download(args.tag, "robots.json"))
    write_data(args.tag, bots, download(args.tag, "LICENSE"), args.output)
    print(f"Wrote {len(bots)} AI bots from ai.robots.txt {args.tag} to {args.output}")


if __name__ == "__main__":
    main()
