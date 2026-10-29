"""Reads mkdocs.yml with `!ENV [NAME, default]` resolved to its default, for the scripts and tests that need a value from it."""
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent


class _Loader(yaml.SafeLoader):
    pass


def _env_default(loader: _Loader, node: yaml.SequenceNode):
    return loader.construct_sequence(node)[-1]


_Loader.add_constructor("!ENV", _env_default)


def site_config() -> dict:
    return yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_Loader)
