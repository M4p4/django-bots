from __future__ import annotations

import json
from importlib.metadata import version
from importlib.resources import files

__version__ = "0.1.0.dev0"

DATA_VERSIONS: dict[str, str] = {
    **json.loads(files(__name__).joinpath("data", "VERSIONS.json").read_text("utf-8")),
    "crawler_user_agents": version("crawler-user-agents"),
    "ua_parser": version("ua-parser"),
    "uap_core": version("ua-parser-builtins"),
}
"""Versions of the bundled and installed data sources."""
