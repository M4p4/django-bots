"""Sphinx configuration for the django-bots documentation."""

from __future__ import annotations

from importlib.metadata import version as package_version

project = "django-bots"
author = "M4p4"
copyright = "2026, M4p4"
release = package_version("django-bots")
version = release

extensions = [
    "myst_parser",
]

source_suffix = {".md": "markdown"}
exclude_patterns = ["_build"]

myst_heading_anchors = 3

html_theme = "furo"
html_title = "django-bots"
