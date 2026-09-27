from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

import pytest

# The maintenance scripts are not part of the installed package, so they are
# imported from the repository checkout by path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ai_bot_diff  # noqa: E402
import bump_version  # noqa: E402
import check_upstream_version  # noqa: E402
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


def write_bots(path, *names):
    path.write_text(json.dumps(dict.fromkeys(names, {})))
    return path


class TestCheckUpstreamVersion:
    @pytest.mark.parametrize(
        ("tag", "expected"),
        [
            ("v1.52", (1, 52)),
            ("1.52", (1, 52)),
            ("v2", (2,)),
            ("v1.53-rc1", None),
            ("latest", None),
        ],
    )
    def test_as_tuple(self, tag, expected):
        assert check_upstream_version.as_tuple(tag) == expected

    def test_latest_version(self, monkeypatch):
        requests = []

        def urlopen(request, timeout):
            requests.append(request)
            return io.BytesIO(b'{"tag_name": "v1.53"}')

        monkeypatch.setattr("urllib.request.urlopen", urlopen)
        monkeypatch.setenv("GITHUB_TOKEN", "secret")

        tag = check_upstream_version.latest_version()

        assert tag == "v1.53"
        assert requests[0].get_header("Authorization") == "Bearer secret"

    def test_latest_version_without_token(self, monkeypatch):
        requests = []

        def urlopen(request, timeout):
            requests.append(request)
            return io.BytesIO(b'{"tag_name": "v1.53"}')

        monkeypatch.setattr("urllib.request.urlopen", urlopen)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        check_upstream_version.latest_version()

        assert not requests[0].has_header("Authorization")

    def test_latest_version_fails(self, monkeypatch):
        def urlopen(request, timeout):
            return io.BytesIO(b"{}")

        monkeypatch.setattr("urllib.request.urlopen", urlopen)

        with pytest.raises(SystemExit, match="Failed to read the latest release"):
            check_upstream_version.latest_version()

    def test_emit_writes_github_output(self, monkeypatch, tmp_path, capsys):
        output = tmp_path / "output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(output))

        check_upstream_version.emit(sync="true", upstream="v1.53")

        assert output.read_text() == "sync=true\nupstream=v1.53\n"
        assert capsys.readouterr().out == "sync=true\nupstream=v1.53\n"

    def test_emit_refuses_newlines(self):
        with pytest.raises(SystemExit, match="containing a newline"):
            check_upstream_version.emit(upstream="v1.53\nsync=true")

    @pytest.mark.parametrize(
        ("upstream", "sync"),
        [
            ("v1.53", "true"),
            ("v1.100", "true"),
            ("v1.52", "false"),
            ("v1.9", "false"),
            ("v1.53-rc1", "false"),
        ],
    )
    def test_main(self, monkeypatch, tmp_path, capsys, upstream, sync):
        versions = tmp_path / "VERSIONS.json"
        versions.write_text('{"ai_robots_txt": "v1.52"}')
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        monkeypatch.setattr(
            sys,
            "argv",
            ["check", "--versions", str(versions), "--upstream", upstream],
        )

        check_upstream_version.main()

        out = capsys.readouterr().out
        assert f"bundled=v1.52\nupstream={upstream}\nsync={sync}\n" in out

    def test_main_queries_github(self, monkeypatch, tmp_path, capsys):
        versions = tmp_path / "VERSIONS.json"
        versions.write_text('{"ai_robots_txt": "v1.52"}')
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        monkeypatch.setattr(check_upstream_version, "latest_version", lambda: "v1.53")
        monkeypatch.setattr(sys, "argv", ["check", "--versions", str(versions)])

        check_upstream_version.main()

        assert "sync=true" in capsys.readouterr().out

    def test_main_rejects_bundled_tag(self, monkeypatch, tmp_path):
        versions = tmp_path / "VERSIONS.json"
        versions.write_text('{"ai_robots_txt": "main"}')
        monkeypatch.setattr(
            sys, "argv", ["check", "--versions", str(versions), "--upstream", "v1"]
        )

        with pytest.raises(SystemExit, match="not a numeric version"):
            check_upstream_version.main()


class TestAIBotDiff:
    def test_summarize_changes(self):
        summary = ai_bot_diff.summarize(
            {"GPTBot", "OldBot"}, {"GPTBot", "newbot", "Abot"}
        )

        assert summary == (
            "2 AI bots before, 3 after.\n"
            "\n"
            "Removed names are no longer blocked or listed in robots.txt output.\n"
            "\n"
            "### Added (2)\n"
            "\n"
            "`Abot`, `newbot`\n"
            "\n"
            "### Removed (1)\n"
            "\n"
            "`OldBot`\n"
        )

    def test_summarize_no_changes(self):
        summary = ai_bot_diff.summarize({"GPTBot"}, {"GPTBot"})

        assert summary == (
            "1 AI bots before, 1 after.\n"
            "\n"
            "No names added or removed; only entry details changed.\n"
        )

    def test_main(self, monkeypatch, tmp_path, capsys):
        before = write_bots(tmp_path / "before.json", "GPTBot")
        after = write_bots(tmp_path / "after.json", "GPTBot", "ClaudeBot")
        monkeypatch.setattr(sys, "argv", ["diff", str(before), "--after", str(after)])

        ai_bot_diff.main()

        assert "### Added (1)\n\n`ClaudeBot`\n" in capsys.readouterr().out


RELEASED = "# Changelog\n\n## 1.0.0 (2026-10-01)\n\n- First release.\n"
PENDING = "# Changelog\n\n## Unreleased\n\n- A feature.\n\n" + RELEASED[13:]


class TestBumpVersion:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.0.0", "1.0.1"),
            ("0.9.19", "0.9.20"),
            ("0.1.0.dev0", None),
            ("1.0.0rc1", None),
        ],
    )
    def test_next_patch(self, version, expected):
        assert bump_version.next_patch(version) == expected

    def test_read_and_set_version(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "x"\nversion = "1.0.0"\n')

        bump_version.set_version(pyproject, "1.0.1")

        assert bump_version.read_version(pyproject) == "1.0.1"
        assert pyproject.read_text() == '[project]\nname = "x"\nversion = "1.0.1"\n'

    def test_read_version_needs_one_line(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('version = "1"\nversion = "2"\n')

        with pytest.raises(SystemExit, match="Found 2 version lines"):
            bump_version.read_version(pyproject)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (RELEASED, False),
            (PENDING, True),
            ("# Changelog\n\n## Unreleased\n\n" + RELEASED[13:], False),
        ],
    )
    def test_has_unreleased_entries(self, text, expected):
        assert bump_version.has_unreleased_entries(text) is expected

    def test_rejects_unknown_changelog(self):
        with pytest.raises(SystemExit, match="does not start with"):
            bump_version.has_unreleased_entries("# History\n")

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                PENDING,
                "# Changelog\n\n## Unreleased\n\n- New.\n- A feature.\n\n"
                + RELEASED[13:],
            ),
            (
                RELEASED,
                "# Changelog\n\n## Unreleased\n\n- New.\n\n" + RELEASED[13:],
            ),
            (
                "# Changelog\n\n## Unreleased\n",
                "# Changelog\n\n## Unreleased\n\n- New.\n",
            ),
        ],
    )
    def test_add_unreleased_entry(self, text, expected):
        assert bump_version.add_unreleased_entry(text, "New.") == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                RELEASED,
                "# Changelog\n\n## 1.0.1 (2026-10-02)\n\n- New.\n\n" + RELEASED[13:],
            ),
            (
                "# Changelog\n\n## Unreleased\n\n" + RELEASED[13:],
                "# Changelog\n\n## Unreleased\n\n## 1.0.1 (2026-10-02)\n\n- New.\n\n"
                + RELEASED[13:],
            ),
            (
                "# Changelog\n",
                "# Changelog\n\n## 1.0.1 (2026-10-02)\n\n- New.\n",
            ),
        ],
    )
    def test_add_release(self, text, expected):
        result = bump_version.add_release(text, "1.0.1", "New.", date(2026, 10, 2))

        assert result == expected

    def test_add_release_refuses_duplicates(self):
        with pytest.raises(SystemExit, match="already has an entry for 1.0.0"):
            bump_version.add_release(RELEASED, "1.0.0", "New.", date(2026, 10, 2))

    def test_entry_text(self):
        assert bump_version.entry_text("v1.53", 3, 1) == (
            "Updated the AI bot list to ai.robots.txt v1.53: 3 added, 1 removed."
        )

    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        before = write_bots(tmp_path / "before.json", "GPTBot", "OldBot")
        after = write_bots(tmp_path / "after.json", "GPTBot", "NewBot", "Abot")
        pyproject = tmp_path / "pyproject.toml"
        changelog = tmp_path / "CHANGELOG.md"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "bump",
                "v1.53",
                "--before",
                str(before),
                "--after",
                str(after),
                "--pyproject",
                str(pyproject),
                "--changelog",
                str(changelog),
            ],
        )
        return pyproject, changelog

    def test_main_bumps_release(self, project, capsys):
        pyproject, changelog = project
        pyproject.write_text('version = "1.0.0"\n')
        changelog.write_text(RELEASED)

        bump_version.main()

        assert pyproject.read_text() == 'version = "1.0.1"\n'
        assert changelog.read_text().startswith(
            f"# Changelog\n\n## 1.0.1 ({date.today().isoformat()})\n\n"
            "- Updated the AI bot list to ai.robots.txt v1.53: 2 added, 1 removed.\n"
        )
        assert capsys.readouterr().out.endswith("release=1.0.1\n")

    @pytest.mark.parametrize(
        ("version", "text"),
        [("0.1.0.dev0", "# Changelog\n\n## Unreleased\n"), ("1.0.0", PENDING)],
    )
    def test_main_keeps_pending_version(self, project, capsys, version, text):
        pyproject, changelog = project
        pyproject.write_text(f'version = "{version}"\n')
        changelog.write_text(text)

        bump_version.main()

        assert pyproject.read_text() == f'version = "{version}"\n'
        assert changelog.read_text().startswith(
            "# Changelog\n\n## Unreleased\n\n"
            "- Updated the AI bot list to ai.robots.txt v1.53: 2 added, 1 removed.\n"
        )
        assert capsys.readouterr().out.endswith("release=\n")
