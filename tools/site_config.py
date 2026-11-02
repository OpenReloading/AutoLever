"""The site's title, description, address and repository (site/site.json, also read by site/docusaurus.config.ts), for the scripts and tests that need them."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def site_config() -> dict:
    return json.loads((ROOT / "site/site.json").read_text(encoding="utf-8"))
