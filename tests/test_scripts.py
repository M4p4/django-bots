from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# The maintenance scripts are not part of the installed package, so they are
# imported from the repository checkout by path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from download_ai_robots import normalize, write_data  # noqa: E402


class TestNormalize:
    def test_sorts_case_insensitively(self):
        raw = json.dumps({"bBot": {}, "Abot": {}, "cbot": {"operator": "x"}}).encode()

        result = normalize(raw)

        assert list(result) == ["Abot", "bBot", "cbot"]
        assert result["cbot"] == {"operator": "x"}

    @pytest.mark.parametrize("raw", [b"[]", b"{}"])
    def test_rejects_non_object(self, raw):
        with pytest.raises(SystemExit, match="non-empty object"):
            normalize(raw)

    @pytest.mark.parametrize("data", [{" ": {}}, {"Bot": "text"}])
    def test_rejects_invalid_entries(self, data):
        with pytest.raises(SystemExit, match="Invalid robots.json entries"):
            normalize(json.dumps(data).encode())


def test_write_data(tmp_path):
    data_dir = tmp_path / "data"

    write_data("v1.2", {"GPTBot": {"operator": "OpenAI"}}, b"MIT License\n", data_dir)

    assert json.loads((data_dir / "ai_robots.json").read_text()) == {
        "GPTBot": {"operator": "OpenAI"}
    }
    assert (
        data_dir / "VERSIONS.json"
    ).read_text() == '{\n  "ai_robots_txt": "v1.2"\n}\n'
    assert (data_dir / "LICENSE-ai-robots-txt").read_bytes() == b"MIT License\n"


def test_vendored_data_is_normalized():
    path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "django_bots"
        / "data"
        / "ai_robots.json"
    )
    raw = path.read_bytes()

    assert list(normalize(raw)) == list(json.loads(raw))
